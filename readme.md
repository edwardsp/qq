# qq - Quick Question

# Overview

This is a simple command line application to ask questions to the Azure OpenAI API.

# Setup

Install the dependencies

    pip install -r requirements.txt

Create the config file with the models.  This will either be `config.json` in the working directory or `$HOME/.qq_config.json`.  Here is the format:

```
{
    "OPENAI_GPT35TURBO_MODEL": "<insert-azure-openai-model-deployment-name>",
    "OPENAI_TEXTDAVINCI003_MODEL": "<insert-azure-openai-model-deployment-name>",
    "OPENAI_CODEDAVINCI002_MODEL": "<insert-azure-openai-model-deployment-name>",
    "OPENAI_API_BASE": "<insert-azure-openai-endpoint>",
    "OPENAI_API_VERSION":"2023-03-15-preview"
}
```

> Note:  All the information is available in the Azure OpenAI resource.  It is not necesary to have all the models listed.  A minimum of one model is required.

# Usage

```
usage: qq.py [-h] [--explain] [--model {gpt35turbo,textdavinci003,codedavinci002}]
             [--temperature TEMPERATURE] [--history]
             [question [question ...]]

Description of your program

positional arguments:
  question              The question to ask

optional arguments:
  -h, --help            show this help message and exit
  --explain, -e         Include an explanation of the returned command
  --model {gpt35turbo,textdavinci003,codedavinci002}, -m {gpt35turbo,textdavinci003,codedavinci002}
                        Choose a model
  --temperature TEMPERATURE, -t TEMPERATURE
                        Set the temperature for the AI model
  --history             Show the history of commands and responses
```
