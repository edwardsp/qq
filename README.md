# qq - Quick Question

# Overview

This is a simple command line application to ask questions to the Azure OpenAI API.

# Setup

Install with pip:

    pip install .

Create the config file with the model.  This will either be `config.json` in the working directory or `~/.qq_config.json`.  Here is the format:

```
{
    "OPENAI_GPT35TURBO_MODEL": <insert-model-deployment-name>,
    "OPENAI_API_BASE": <insert-azure-openai-endpoint>,
    "OPENAI_API_VERSION":"2023-07-01-preview"
}
```

> Note:  All the information is available in the Azure OpenAI resource.  A minimum of one model is required.

# Usage

```
$ qq -h
usage: qq [-h] [-v {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [--explain] [--model {gpt35turbo}] [--temperature TEMPERATURE] [--history]
          [question [question ...]]

Ask a quick question from the terminal

positional arguments:
  question              The question to ask

optional arguments:
  -h, --help            show this help message and exit
  -v {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --verbosity {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging verbosity level (default: INFO)
  --explain, -e         Include an explanation of the returned command
  --model {gpt35turbo}, -m {gpt35turbo}
                        Choose a model
  --temperature TEMPERATURE, -t TEMPERATURE
                        Set the temperature for the AI model
  --history             Show the history of commands and responses
```
