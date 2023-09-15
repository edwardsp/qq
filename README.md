# qq - Quick Question

# Overview

This is a simple command line application to ask questions to the Azure OpenAI API.  The OS and shell are detected and the command returned is for the current environment.  The command is put in the clipboard for easy pasting without needing to take the hands off the keyboard.

# Pre-requisites

You will need a OpenAI model deployed on Azure.  Follow instructions [here](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/create-resource?pivots=web-portal).

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
usage: qq [-h] [-v {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [--explain [EXPLAIN]] [--model {gpt35turbo}] [--temperature TEMPERATURE] [--history] [question [question ...]]

Ask a quick question from the terminal

positional arguments:
  question              The question to ask

optional arguments:
  -h, --help            show this help message and exit
  -v {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --verbosity {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging verbosity level (default: INFO)
  --explain [EXPLAIN], -e [EXPLAIN]
                        Give an explanation for the command. Either leave blank for the previous command or use the index from the history command.
  --model {gpt35turbo}, -m {gpt35turbo}
                        Choose a model
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
Get-ChildItem -Recurse | Where-Object { $_.Length -ge 1KB -and $_.Length -le 10KB }
```

Getting an explanation for the last command:

```
PS> qq -e
Question:  find all files between 1KB and 10KB below the current directory
Answer:  Get-ChildItem -Recurse | Where-Object { $_.Length -ge 1KB -and $_.Length -le 10KB }
Explanation:
The command provided is using PowerShell to find all files between 1KB and 10KB below the current directory.

Here is a breakdown of how the command works:

1. `Get-ChildItem -Recurse`: This command is used to retrieve all files and directories below the current directory. The `-Recurse` parameter ensures that all subdirectories are also included in the search.

2. `Where-Object { $_.Length -ge 1KB -and $_.Length -le 10KB }`: This part of the command filters the results obtained from the previous step. The `Where-Object` cmdlet is used to specify a condition that each file must meet in order to be included in the final output.

   - `$_` represents the current object being evaluated, which in this case is each file.
   - `$_.Length` retrieves the size of each file in bytes.
   - `-ge` is the comparison operator for "greater than or equal to".
   - `-le` is the comparison operator for "less than or equal to".
   - `1KB` and `10KB` are the size limits specified in kilobytes.

   Therefore, the condition `{ $_.Length -ge 1KB -and $_.Length -le 10KB }` ensures that only files with a size between 1KB and 10KB (inclusive) are selected.

In summary, the command retrieves all files and directories below the current directory and then filters the results to only include files with a size between 1KB and 10KB.
```
