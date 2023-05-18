
Install the dependencies

    pip install -r requirements.txt

Create the config file with the models.  Here is the format:

```
{
    "OPENAI_GPT35TURBO_MODEL": "<insert-model-deployment-name>",
    "OPENAI_TEXTDAVINCI003_MODEL": "<insert-model-deployment-name>",
    "OPENAI_CODEDAVINCI002_MODEL": "<insert-model-deployment-name>",
    "OPENAI_API_BASE": "<insert-azure-openai-endpoint>",
    "OPENAI_API_VERSION":"2023-03-15-preview"
}
```

Notes:

* Replace `https://xxxxx.openai.azure.com/` with your Azure OpenAI endpoint
* Put the model names you create in your Azure OpenAI resource for the `OPENAI_xxx_MODEL` parameters
* Only one model is required in order to run

