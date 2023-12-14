#!/usr/bin/env python3

import argparse
import datetime
import functools
import json
import logging
import openai
import os
import platform
import psutil
import pyperclip
import sqlite3
import sys
from rich import print as rprint
from rich.logging import RichHandler
from rich.panel import Panel
from rich.progress import Progress
from typing import Dict, Union

logger = logging.getLogger('qq')

conn = sqlite3.connect(os.path.join(os.path.expanduser("~"), '.qq_history.db'))

def detect_os() -> str:
    system = platform.system()
    if system == 'Linux':
        return 'Linux'
    elif system == 'Windows':
        return 'Windows'
    elif system == 'Darwin':
        return 'macOS'
    else:
        return 'Unknown'

def detect_shell() -> str:
    parent_pid = os.getppid()
    parent_name = psutil.Process(parent_pid).name()
    if parent_name == "qq.exe":
        parent_name = psutil.Process(parent_pid).parent().name()
    logger.debug(parent_name)
    return parent_name.split('/')[-1]

def detect_linux_distro() -> Union[str, None]:
    try:
        logger.debug("Detecting Linux distro")
        distroinfo = platform.freedesktop_os_release()

        namestr = distroinfo.get('PRETTY_NAME', None)
        if namestr:
            logger.debug("Found PRETTY_NAME %s", namestr)
            return namestr

        namestr = (distroinfo.get('NAME', None) or
                    distroinfo.get('ID', None) or
                    distroinfo.get('ID_LIKE', None))

        if namestr:
            logger.debug("Found a distro name %s", namestr)
            versionstr = (distroinfo.get('VERSION', None) or
                            distroinfo.get('VERSION_ID', None))
            if versionstr:
                logger.debug("Found a distro version %s", versionstr)
                namestr = f"{namestr} {versionstr}"

        logger.debug("Composed a distro name %s", namestr)
        return namestr

    except:
        return None

def get_environment_description() -> str:
    detected_os = detect_os()
    detected_shell = detect_shell()
    detected_linux_distro = detect_linux_distro()
    return f"""
OS: {detected_os}
{f"Linux Distro: {detected_linux_distro}" if detected_linux_distro else ""}
Shell: {detected_shell}
"""

def error_and_exit(message) -> None:
    logger.error(message)
    sys.exit(1)

system_prompt = "You are a tool designed to help users run commands in the terminal. Only use the functions you have been provided with.  Do not include the command to run the shell unless it is different to the one running."
system_prompt_verbose = "You are an assistant for users running commands in the terminal.  Answer with just the simple shell instructions and provide an explanation."

# List of models that are supported, taken from the /v1/chat/completions endpoint list
# https://platform.openai.com/docs/models/model-endpoint-compatibility
# Removed all snapshot versions, first version is used as the default
supported_models = [
    "gpt-3.5-turbo",
    "gpt-4",
    "gpt-3.5-turbo-16k",
    "gpt-4-32k",
    "gpt-4-1106-preview",
]

def setup_database():
    conn.execute('''CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP,
                    question TEXT,
                    response TEXT,
                    paste_buffer TEXT
                )''')

def get_history_item(id):
    conn.row_factory = sqlite3.Row
    if not id or id <= 0:
        cursor = conn.execute("SELECT * FROM history ORDER BY timestamp DESC LIMIT 1")
    else:
        cursor = conn.execute("SELECT * FROM history WHERE id = ?", (id,))
    rows = cursor.fetchall()
    if len(rows) == 0:
        logger.error(f"No history item found with id {id}")
        sys.exit(1)
    return (rows[0]['question'], rows[0]['response'], rows[0]['paste_buffer'])

def append_to_history(question, response, paste_buffer):
    timestamp = datetime.datetime.now().replace(microsecond=0)
    conn.execute("INSERT INTO history (timestamp, question, response, paste_buffer) VALUES (?, ?, ?, ?)", (timestamp, question, response, paste_buffer))
    conn.commit()

def show_history(max_items=100):
    # Only import when needed to avoid slowing down startup
    from rich.table import Table
    from rich.console import Console

    table = Table(title = "QQ History", show_header=True, header_style="bold magenta", highlight=True)
    table.add_column("ID", justify="right", style="dim", width=len(str(max_items)))
    table.add_column("Timestamp", justify="center", style="dim")
    table.add_column("Question", justify="left")
    table.add_column("Answer", justify="left")

    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT * FROM history ORDER BY timestamp DESC LIMIT ?", (max_items,))
    rows = cursor.fetchall()
    for row in rows[::-1]:
        table.add_row(str(row['id']), row['timestamp'], row['question'], row['response'])

    Console().print(table)

def openai_chat_completion(model, prompt, question, functions, function_call, temperature):
    logger.debug(f"Prompt: {prompt}")
    logger.debug(f"model: {model}")
    logger.debug(f"question: {question}")
    func_args = {
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": question}
        ],
        "temperature": temperature
    }
    if openai.api_type == 'azure':
        func_args['engine'] = model
    elif openai.api_type == 'open_ai':
        func_args['model'] = model
    else:
        error_and_exit(f"Invalid API type: {open_ai.api_type}")
    if len(functions) > 0:
        func_args['functions'] = functions
        func_args['function_call'] = function_call

    try:
        response = openai.chat.completions.create(**func_args)
        return response.choices[0].message

    except openai.error.APIError as e:
        logger.error(f"OpenAI API returned an API Error: {e}")
        sys.exit(1)
    except openai.error.AuthenticationError as e:
        logger.error(f"OpenAI API returned an Authentication Error: {e}")
        sys.exit(1)
    except openai.error.APIConnectionError as e:
        logger.error(f"Failed to connect to OpenAI API: {e}")
        sys.exit(1)
    except openai.error.InvalidRequestError as e:
        logger.error(f"Invalid Request Error: {e}")
        sys.exit(1)
    except openai.error.RateLimitError as e:
        logger.error(f"OpenAI API request exceeded rate limit: {e}")
        sys.exit(1)
    except openai.error.ServiceUnavailableError as e:
        logger.error(f"Service Unavailable: {e}")
        sys.exit(1)
    except openai.error.Timeout as e:
        logger.error(f"Request timed out: {e}")
        sys.exit(1)
    except:
        logger.exception(f"An unknown exception has occurred: {e}")
        sys.exit(1)

def ask_chat_completion_question(model, question, paste_buffer, temperature):
    prompt = f"""
You are a tool designed to help users run commands in the terminal.
Only use the functions you have been provided with.
Do not include the command to run the shell unless it is different to the one running.
Format the command in a way that typical placeholder values are used if required, such as <filename> or <username> for required arguments, and [filename] or [username] for optional arguments.

{get_environment_description()}
"""
    if paste_buffer:
        prompt += f"""
All the following text is in the paste buffer which may or may not be relevant to the question:
{paste_buffer}
"""
    functions = [
        {
            "name": "run_command",
            "description": "The command that should be run",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string", 
                        "description": "The command to run"
                    }
                }
            },
        }
    ]
    function_call = {"name": "run_command"}

    answer = openai_chat_completion(model, prompt, question, functions, function_call, temperature)
    
    if not hasattr(answer, 'function_call'):
        logger.debug(answer)
        error_and_exit("Cannot process the response, missing function_call.")

    if answer.function_call.name != 'run_command':
        error_and_exit(f"Invalid function requested: {answer.function_call.name}")
    try:
        args = json.loads(answer.function_call.arguments)
    except Exception as e:
        logger.exception(f"Invalid JSON arguments returned from the function API - {answer.function_call.arguments}\n{e}")
        sys.exit(1)

    if 'command' not in args:
        error_and_exit("Missing command argument in run_command function call.")
    return args['command']

    
def ask_chat_completion_explanation(model, question, answer, paste_buffer, temperature):
    detected_os = detect_os()
    detected_shell = detect_shell()
    prompt = f"""
You are a tool designed to help users run commands in the terminal.
You will be provided a question and an answer that was previously given.
Provide an explanation for how the command works to solve the original question.
{get_environment_description()}
"""
    if paste_buffer:
        prompt += f"""
All the following text is in the paste buffer which may or may not be relevant to the question.  If you need to use it, explain why in the answer:
{paste_buffer}
"""
    question = f"""
    Provide an explanation for the following:
    Question: {question}
    Answer: {answer}
    """
    answer = openai_chat_completion(model, prompt, question, [], None, temperature)
    if hasattr(answer, 'content'):
        return answer.content

    logger.debug(answer)
    logger.error("Cannot process the response.")
    sys.exit(1)

@functools.lru_cache
def load_configfile() -> Dict[str, str]:
    """
    Look for `config.json` in the current directory first otherwise ~/.qq_config.json
    """
    locations = (
        os.path.join(os.getcwd(), 'config.json'),
        os.path.join(os.path.expanduser("~"), '.qq_config.json')
    )
    try:
        for config_file_name in locations:
            logger.debug("Looking for config file: {config_file_name}")
            if not os.path.exists(config_file_name):
                continue
            logger.info("Using config file: {config_file_name}")
            with open(config_file_name) as config_file:
                config_details = json.load(config_file)
                return config_details
    except Exception as e:
        logger.exception(f"Failed to load config file")
        sys.exit(1)

    logger.error("No config file found.")
    sys.exit(1)

@functools.lru_cache
def get_config_value(config_name: str, default_value = None):
    config_data = load_configfile()

    # Check environment variables first, then config file, last return default value
    config_value = os.getenv(config_name)
    if config_value:
        return config_value

    config_value = config_data.get(config_name, default_value)
    if config_value:
        return config_value
    error_and_exit(f"Config value {config_name} not found.")

def quickquestion():
    setup_database()

    # Defaulting to Azure for backwards compatibility, set to open_ai for the OpenAI API
    openai.api_type = get_config_value('OPENAI_API_TYPE', 'azure').lower()
    openai.api_key = get_config_value("OPENAI_API_KEY")

    openai_model = get_config_value('OPENAI_MODEL')
    if openai.api_type == 'azure':
        openai.api_base = get_config_value('OPENAI_API_BASE')
        openai.api_version = get_config_value('OPENAI_API_VERSION')
    elif openai.api_type == 'open_ai':
        openai.organization = get_config_value('OPENAI_ORGANIZATION')
        if openai_model not in supported_models:
            logger.warning(f"Configured model {openai_model} is not in the list of supported models.")



    parser = argparse.ArgumentParser(description='Ask a quick question from the terminal')
    parser.add_argument(
        "-v",
        "--verbosity",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging verbosity level (default: INFO)",
    )
    parser.add_argument('--explain', '-e', help='Give an explanation for the command.  Either leave blank for the previous command or use the index from the history command.', type=int, default=0, nargs='?')
    parser.add_argument('--temperature', '-t', help='Set the temperature for the AI model', default=0.0, type=float)
    parser.add_argument('--history', help='Show the history of commands and responses', action='store_true')
    parser.add_argument('--paste', '-p', help='Send the paste buffer as part of the input', action='store_true')
    parser.add_argument('question', nargs='*', help='The question to ask')

    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.verbosity),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[RichHandler(rich_tracebacks=True)],
    )

    if args.history:
        show_history()
    elif args.explain != 0:
        q, a, paste_buffer = get_history_item(args.explain)
        rprint(Panel(q, title="Question"))
        rprint(Panel(a, title="Answer"))
        with Progress(transient=True) as progress:
            progress.add_task("Generating explanation...", total=None)
            rprint(Panel(ask_chat_completion_explanation(openai_model, q, a, paste_buffer, args.temperature), title="Explanation"))
        
    else:
        q = args.question
        if args.question:
            q = ' '.join(args.question)
        else:
            from rich.prompt import Prompt
            q = Prompt.ask("What command are you looking for")
        with Progress(transient=True) as progress:
            progress.add_task("Generating answer...", total=None)
            paste_buffer = ""
            if args.paste:
                paste_buffer = pyperclip.paste()
            a = ask_chat_completion_question(openai_model, q, paste_buffer, args.temperature)
        rprint(a)
        pyperclip.copy(a)
        append_to_history(q, a, paste_buffer)

if __name__ == "__main__":
    quickquestion()
    
