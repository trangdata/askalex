import os
import openai
import numpy as np
from dotenv import load_dotenv

load_dotenv()
client = openai.AzureOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    api_version=os.getenv("OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("OPENAI_API_BASE"),
)


def get_embedding(text, model="text-embedding-ada-002"):
    text = text.replace("\n", " ")
    return client.embeddings.create(input=[text], model=model).data[0].embedding


def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


# estimate the cost of the request
# https://azure.microsoft.com/en-us/pricing/details/cognitive-services/openai-service/
def estimate_cost(result):
    try:
        model = result.model
        prompt_tokens = result.usage.prompt_tokens
        completion_tokens = result.usage.completion_tokens
    except:
        raise ValueError("Unable to parse result: %s" % str(result))

    # cheapest to most expensive. completion tokens are more costly than prompt tokens
    if model == "gpt-35-turbo":
        est_cost = (0.0015 * prompt_tokens + 0.002 * completion_tokens) / 1000.0
    elif model == "gpt-35-turbo-16k":  # 2x more expensive than 3.5-turbo
        est_cost = (0.003 * prompt_tokens + 0.004 * completion_tokens) / 1000.0
    elif model == "gpt-4":  # 20x-30x more expensive than 3.5-turbo
        est_cost = (0.03 * prompt_tokens + 0.06 * completion_tokens) / 1000.0
    elif model == "gpt-4-32k":  # 40x-60x more expensive than 3.5-turbo
        est_cost = (0.06 * prompt_tokens + 0.12 * completion_tokens) / 1000.0
    else:
        raise ValueError("No cost information for that model" % str(model))

    return est_cost, prompt_tokens, completion_tokens
