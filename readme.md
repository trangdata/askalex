
# AskAlex

AskAlex is a minimal Python Shiny app that integrates [OpenAI](https://platform.openai.com/docs) and [OpenAlex](https://openalex.org/) knowledge graph to optimize literature aggregation.

Given a scientific question from the user, AskAlex searches the OpenAlex database for 100 most relevant articles, uses semantic search to find the best 10 abstracts, and includes them in the prompt sent to OpenAI along with your original question.
Output is the OpenAI response and relevant articles.

![AskAlex-workflow](diagram.png)

Currently, the app works with [Azure OpenAI endpoints](https://learn.microsoft.com/en-us/azure/ai-services/openai/reference).

## ⚙️ Setup

Assuming you have `conda` installed, you first want to create a new conda environment named `askalex` and install the necessary dependencies:

``` sh
conda create --name askalex
conda activate askalex
conda install pip
pip install -r requirements.txt
```

You will also need the following environment variables in your `.env` file:
```
OPENAI_API_TYPE = azure
OPENAI_API_KEY
OPENAI_API_BASE
OPENAI_API_VERSION = 2023-05-15
APP_RUN = local # or connect_server
```

and optionally:
```
OPENAI_PROXY 
OPENALEX_API_KEY 
COMPANY_PROXY
COMPANY_NO_PROXY
```

Finally, you may need to modify the `model_engine_dict` variable in [`app.py`](app.py) to match the your company's available models on Azure.


## 🌿 Run app

``` sh
# conda activate askalex
shiny run --port 56486 --reload app.py
```

## 🛤️ Roadmap

- fix token issue for text-davinci-003
- use openai endpoint
- add community key for public use
- incorporate full text?
- improve OpenAlex search (currently performing abstract search)

## 🤝 Contributing

Thank you for considering contributing!
Please open an issue to discuss a contribution you'd like to implement to make this app better.
