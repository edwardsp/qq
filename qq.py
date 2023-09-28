#!/usr/bin/env python3

import argparse
import datetime
import json
import logging
import openai
import os
import platform
import psutil
import pyperclip
import sqlite3
import sys

logger = logging.getLogger('qq')

conn = sqlite3.connect(os.path.join(os.path.expanduser("~"), '.qq_history.db'))

def detect_os():
    system = platform.system()
    if system == 'Linux':
        return 'Linux'
    elif system == 'Windows':
        return 'Windows'
    elif system == 'Darwin':
        return 'macOS'
    else:
        return 'Unknown'

def detect_shell():
    parent_pid = os.getppid()
    parent_name = psutil.Process(parent_pid).name()
    if parent_name == "qq.exe":
        parent_name = psutil.Process(parent_pid).parent().name()
    logger.debug(parent_name)
    return parent_name.split('/')[-1]

system_prompt = "You are a tool designed to help users run commands in the terminal. Only use the functions you have been provided with.  Do not include the command to run the shell unless it is different to the one running."
system_prompt_verbose = "You are an assistant for users running commands in the terminal.  Answer with just the simple shell instructions and provide an explanation."

def setup_database():
    conn.execute('''CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP,
                    question TEXT,
                    response TEXT
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
    return (rows[0]['question'], rows[0]['response'])

def append_to_history(question, response):
    timestamp = datetime.datetime.now()
    conn.execute("INSERT INTO history (timestamp, question, response) VALUES (?, ?, ?)", (timestamp, question, response))
    conn.commit()

def get_history(max_items=100):
    filename = os.path.join(os.path.expanduser("~"), '.qq_history.json')
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT * FROM history ORDER BY timestamp DESC LIMIT ?", (max_items,))
    rows = cursor.fetchall()
    hist = []
    for row in rows[::-1]:
        i = row['id']
        q = row['question']
        a = row['response'].replace("\n", " ")

        try:
            full_width = os.get_terminal_size().columns
        except:
            full_width = 80

        # 5 digits for the index, 2 spaces, 2 brackets, 2 spaces
        padding = 5 + 2 + 2 + 2
        width = full_width - padding
        q_width = width // 2
        a_width = width - q_width

        qlen = len(q)
        alen = len(a)

        if qlen > q_width:
            if alen > a_width:
                a = a[:a_width-3] + "..."
                q = q[:q_width-3] + "..."
            else:
                if width - alen < qlen:
                    q = q[:width-alen-3] + "..."
        else:
            if width - qlen < alen:
                a = a[:width-qlen-3] + "..."

        hist.append(f"{i:5}  {q}  [{a}]")
    return "\n".join(hist)

def openai_chat_completion(model, prompt, question, functions, function_call, temperature):
    logger.debug(f"Prompt: {prompt}")
    logger.debug(f"model: {model}")
    logger.debug(f"question: {question}")
    func_args = {
        "engine": model,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": question}
        ],
        "temperature": temperature
    }
    if len(functions) > 0:
        func_args['functions'] = functions
        func_args['function_call'] = function_call

    try:
        response = openai.ChatCompletion.create(**func_args)
        return response['choices'][0]['message']
        
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
        logger.error("An exception has occured.")
        sys.exit(1)

def ask_chat_completion_question(model, question, temperature):
    detected_os = detect_os()
    detected_shell = detect_shell()
    prompt = f"""
    You are a tool designed to help users run commands in the terminal.  Only use the functions you have been provided with.  Do not include the command to run the shell unless it is different to the one running.
    
    OS: {detected_os}
    Shell: {detected_shell}
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
    
    if 'function_call' in answer:
        if answer['function_call']['name'] != 'run_command':
            logger.error(f"Invalid function requested: {answer['function_call']['name']}")
            sys.exit(1)
        try:
            args = json.loads(answer['function_call']['arguments'])
        except:
            logger.error(f"Invalid JSON arguments returned from the function API - {answer['function_call']['arguments']}")
            sys.exit(1)
        if 'command' not in args:
            logger.error("Missing command argument in run_command function call.")
            sys.exit(1)
        return args['command']

    logger.debug(answer)
    logger.error("Cannot process the response.")
    sys.exit(1)
    
def ask_chat_completion_explanation(model, question, answer, temperature):
    detected_os = detect_os()
    detected_shell = detect_shell()
    prompt = f"""
    You are a tool designed to help users run commands in the terminal.  You will be provided a question and an answer that was previously given.  Provide an explanation for how the command works to solve the original question.
    
    OS: {detected_os}
    Shell: {detected_shell}
    """
    question = f"""
    Provide an explanation for the following:
    Question: {question}
    Answer: {answer}
    """
    answer = openai_chat_completion(model, prompt, question, [], None, temperature)
    if 'content' in answer:
        return answer['content']

    logger.debug(answer)
    logger.error("Cannot process the response.")
    sys.exit(1)

def find_config():
    # look for `config.json` in the current directory first otherwise ~/.qq_config.json
    config_file = os.path.join(os.getcwd(), 'config.json')
    logger.debug("Looking for config file: {config_file}")
    if os.path.exists(config_file):
        logger.info("Using config file: {config_file}")
        return config_file
    
    config_file = os.path.join(os.path.expanduser("~"), '.qq_config.json')
    logger.debug("Looking for config file: {config_file}")
    if os.path.exists(config_file):
        logger.info("Using config file: {config_file}")
        return config_file
    
    logger.ERROR("No config file found.")
    sys.exit(1)

def quickquestion():
    setup_database()

    config_filename = find_config()
    # Load config values
    with open(config_filename) as config_file:
        config_details = json.load(config_file)
    
    openai.api_type = "azure"
    openai.api_key = os.getenv("OPENAI_API_KEY")
    openai.api_base = config_details['OPENAI_API_BASE']
    openai.api_version = config_details['OPENAI_API_VERSION']

    model_choices = []
    if 'OPENAI_GPT35TURBO_MODEL' in config_details:
        model_choices.append('gpt35turbo')

    if len(model_choices) == 0:
        print("No models are configured. Please add a model to your config.json file.")
        exit(1)

    parser = argparse.ArgumentParser(description='Ask a quick question from the terminal')
    parser.add_argument(
        "-v",
        "--verbosity",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging verbosity level (default: INFO)",
    )
    parser.add_argument('--explain', '-e', help='Give an explanation for the command.  Either leave blank for the previous command or use the index from the history command.', type=int, default=0, nargs='?')
    parser.add_argument('--model', '-m', choices=model_choices, default=model_choices[0], help='Choose a model')
    parser.add_argument('--temperature', '-t', help='Set the temperature for the AI model', default=0.0, type=float)
    parser.add_argument('--history', help='Show the history of commands and responses', action='store_true')
    parser.add_argument('question', nargs='*', help='The question to ask')

    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.verbosity),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.debug(f"Config file: {config_filename}")
    logger.debug(f"Config details: {config_details}")

    if args.history:
        print(get_history())
        exit(0)

    explain = (args.explain != 0)

    if explain:
        q, a = get_history_item(args.explain)
    else:
        q = ' '.join(args.question)

    if args.model == 'gpt35turbo':
        model = config_details['OPENAI_GPT35TURBO_MODEL']
        if explain:
            print("Question: ", q)
            print("Answer: ", a)
            print("Explanation:")
            a = ask_chat_completion_explanation(model, q, a, args.temperature)
        else:
            a = ask_chat_completion_question(model, q, args.temperature)
    else:
        logger.error(f"Unknown model: {args.model}")
        exit(1)

    print(a)

    if not explain:
        pyperclip.copy(a)
        append_to_history(q, a)

if __name__ == "__main__":
    quickquestion()
    