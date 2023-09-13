#!/usr/bin/env python3

import argparse
import datetime
import json
import logging
import openai
import os
import platform
import psutil
import sqlite3

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

def append_to_history(question, response):
    timestamp = datetime.datetime.now()
    conn.execute("INSERT INTO history (timestamp, question, response) VALUES (?, ?, ?)", (timestamp, question, response))
    conn.commit()

def get_history(max_items=100):
    filename = os.path.join(os.path.expanduser("~"), '.qq_history.json')
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT * FROM history ORDER BY timestamp LIMIT ?", (max_items,))
    rows = cursor.fetchall()
    hist = []
    for row in rows:
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

def ask_chat_completion(model, question, explanation=False, temperature=0.0):
    detected_os = detect_os()
    detected_shell = detect_shell()
    prompt = f"""
    {system_prompt_verbose if explanation else system_prompt}
    
    OS: {detected_os}
    Shell: {detected_shell}
    """
    logger.debug(f"Prompt: {prompt}")
    logger.debug(f"model: {model}")
    try:
        response = openai.ChatCompletion.create(
            engine=model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": question}
            ],
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
            ],
            temperature=temperature,
            function_call="none" if explanation else {"name": "run_command"}
        )
        answer = response['choices'][0]['message']
        if 'function_call' in answer:
            if answer['function_call']['name'] != 'run_command':
                return f"Invalid function requested: {answer['function_call']['name']}"
            try:
                args = json.loads(answer['function_call']['arguments'])
            except:
                return f"Invalid JSON arguments returned from the function API - {answer['function_call']['arguments']}"
            if 'command' not in args:
                return "Missing command argument in run_command function call."
            return args['command']
        elif 'content' in answer:
            return answer['content']

        print(answer)
        return "Cannot process the response."
        
    except openai.error.APIError as e:
        # Handle API error here, e.g. retry or log
        return(f"OpenAI API returned an API Error: {e}")

    except openai.error.AuthenticationError as e:
        # Handle Authentication error here, e.g. invalid API key
        return(f"OpenAI API returned an Authentication Error: {e}")

    except openai.error.APIConnectionError as e:
        # Handle connection error here
        return(f"Failed to connect to OpenAI API: {e}")

    except openai.error.InvalidRequestError as e:
        # Handle connection error here
        return f"Invalid Request Error: {e}"

    except openai.error.RateLimitError as e:
        # Handle rate limit error
        return f"OpenAI API request exceeded rate limit: {e}"

    except openai.error.ServiceUnavailableError as e:
        # Handle Service Unavailable error
        return f"Service Unavailable: {e}"

    except openai.error.Timeout as e:
        # Handle request timeout
        return f"Request timed out: {e}"
        
    except:
        # Handles all other exceptions
        return "An exception has occured."

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
    parser.add_argument('--explain', '-e', help='Include an explanation of the returned command', action='store_true')
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

    q = ' '.join(args.question)

    if args.model == 'gpt35turbo':
        model = config_details['OPENAI_GPT35TURBO_MODEL']
        a = ask_chat_completion(model, q, args.explain, args.temperature)
    else:
        print(f"Unknown model: {args.model}")
        exit(1)

    print(a)
    append_to_history(q, a)

if __name__ == "__main__":
    quickquestion()
    