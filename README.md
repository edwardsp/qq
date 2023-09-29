# qq - Quick Question

# Overview

This is a simple command line application to ask questions to the Azure OpenAI API.  The OS and shell are detected and the command returned is for the current environment.  The command is put in the clipboard for easy pasting without needing to take the hands off the keyboard.

# Pre-requisites

You will need access to an Open AI chat completion model.  Currently, the models supported are:

* gpt-3.5-turbo
* gpt-4
* gpt-3.5-turbo-16k
* gpt-4-32k

The model can be from either OpenAI or Azure OpenAI.  For instructions on deploying a model to Azure OpenAI, see [here](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/create-resource?pivots=web-portal).

# Setup

Install with pip:

    pip install .

Create the config file.  This can either be `config.json` in the working directory or `~/.qq_config.json`.  Any of the options can be set through an environment variable.  Here is the format for Azure OpenAI:

```
{
    "OPENAI_API_TYPE": "azure",
    "OPENAI_API_BASE": "<insert-azure-openai-endpoint>",
    "OPENAI_MODEL": "<insert-model-deployment-name>",
    "OPENAI_API_KEY": "<insert-openai-api-key>",
    "OPENAI_API_VERSION":"2023-07-01-preview"
}
```

And, this is the format for OpenAI:

```
{
    "OPENAI_API_TYPE": "open_ai",
    "OPENAI_ORGANIZATION": "<insert-openai-org-id>",
    "OPENAI_API_KEY": "<insert-openai-key>",
    "OPENAI_MODEL": "<insert-openai-model-name>"
}
```

> Note:  All the information is available in either your OpenAI or Azure OpenAI account.

# Usage

```
$ qq -h
usage: qq [-h] [-v {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [--explain [EXPLAIN]]
          [--temperature TEMPERATURE] [--history]
          [question [question ...]]

Ask a quick question from the terminal

positional arguments:
  question              The question to ask

optional arguments:
  -h, --help            show this help message and exit
  -v {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --verbosity {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging verbosity level (default: INFO)
  --explain [EXPLAIN], -e [EXPLAIN]
                        Give an explanation for the command. Either leave blank for the previous
                        command or use the index from the history command.
  --temperature TEMPERATURE, -t TEMPERATURE
                        Set the temperature for the AI model
  --history             Show the history of commands and responses
```

# Examples

## Bash

Find files between 1KB and 10KB

```
$ qq find all files between 1KB and 10KB below the current directory
find . -type f -size +1k -size -10k
```

## PowerShell

Find files between 1KB and 10KB

```
PS> qq find all files between 1KB and 10KB below the current directory
Get-ChildItem -Recurse | Where-Object {($_.Length/1KB) -gt 1 -and ($_.Length/1KB) -lt 10}
```

Getting an explanation for the last command:

```
PS> qq -e
╭───────────────────────────────────────── Question ──────────────────────────────────────────╮
│ find all files between 1KB and 10KB below the current directory                             │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯
╭────────────────────────────────────────── Answer ───────────────────────────────────────────╮
│ Get-ChildItem -Recurse | Where-Object {($_.Length/1KB) -gt 1 -and ($_.Length/1KB) -lt 10}   │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯
╭──────────────────────────────────────── Explanation ────────────────────────────────────────╮
│ The command provided is a PowerShell command used to find all files in the current          │
│ directory and its subdirectories that are between 1KB and 10KB in size.                     │
│                                                                                             │
│ Here's a breakdown of how it works:                                                         │
│                                                                                             │
│ - `Get-ChildItem -Recurse`: This is the initial command that starts the process.            │
│ `Get-ChildItem` is a cmdlet in PowerShell that gets the items (files, directories) in one   │
│ or more specified locations. The `-Recurse` parameter tells PowerShell to get items in all  │
│ child containers (subdirectories) of the location specified, not just the current           │
│ directory.                                                                                  │
│                                                                                             │
│ - `|`: This is the pipeline operator in PowerShell. It takes the output from the command on │
│ its left (in this case, `Get-ChildItem -Recurse`) and passes it as input to the command on  │
│ its right.                                                                                  │
│                                                                                             │
│ - `Where-Object {($_.Length/1KB) -gt 1 -and ($_.Length/1KB) -lt 10}`: This is the command   │
│ that filters the output from `Get-ChildItem -Recurse`. `Where-Object` is a cmdlet that      │
│ filters input from the pipeline. In this case, it's filtering based on the size of the      │
│ files.                                                                                      │
│                                                                                             │
│     - `$_.Length/1KB`: This expression gets the size of each file in kilobytes. `$_` is a   │
│ variable in PowerShell that represents the current object in the pipeline (in this case,    │
│ each file). `.Length` is a property of file objects that represents their size in bytes, so │
│ dividing by 1KB converts the size to kilobytes.                                             │
│                                                                                             │
│     - `-gt 1 -and -lt 10`: These are the conditions that the file sizes must meet to pass   │
│ the filter. `-gt 1` means "greater than 1KB", `-lt 10` means "less than 10KB", and `-and`   │
│ is a logical operator that requires both conditions to be true. So, only files that are     │
│ more than 1KB and less than 10KB in size will pass the filter and be included in the        │
│ output.                                                                                     │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯
```
