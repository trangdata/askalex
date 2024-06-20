import numpy as np
from openai_utils import get_embedding, client, estimate_cost


def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def create_context(question, df, max_len=1800, size="ada"):
    """
    Create a context for a question by finding the most similar context from the dataframe
    """

    q_embeddings = get_embedding(question)
    df["similarities"] = df.embedding.apply(
        lambda x: cosine_similarity(x, q_embeddings)
    )

    returns = []
    cur_len = 0

    # Sort by distance and add the text to the context until the context is too long
    for i, row in df.sort_values("similarities", ascending=False).iterrows():
        # Add the length of the text to the current length
        cur_len += row["n_tokens"] + 4

        # If the context is too long, break
        if cur_len > max_len:
            break

        # Else add it to the text that is being returned
        returns.append(row["abstract"])

    # Return the context
    return "\n\n###\n\n".join(returns)


def answer_question(
    question,
    df,
    model="gpt-35-turbo",  # "GPT-4-32k",
    max_len=4097,
    size="ada",
    debug=False,
    stop_sequence=None,
):
    """
    Answer a question based on the most similar context from the dataframe texts
    """
    if question is None:
        return ""

    template = (
        "You are an intelligent assistant helping users with their questions. "
        + "Use 'you' to refer to the individual asking the questions even if they ask with 'I'. "
        + "Answer the following question using only the data provided in the sources below. "
        + "For tabular information return it as an html table. Do not return markdown format. "
        + "If you cannot answer using the sources below, say you don't know. "
        + "\n\nContext: {context}\n\n---\n\nQuestion: {question}\nAnswer: "
    )

    context = create_context(
        question,
        df,
        max_len=max_len,
        size=size,
    )
    # If debug, print the raw model response
    if debug:
        print("Context:\n" + context)
        print("\n\n")

    prompt = template.format(context=context, question=question)
    try:
        result = complete_model(prompt, model, stop_sequence)
        return trim_incomplete_sentence(result[0]), result[1]
    except Exception as e:
        print(e)
        return ""


def get_keywords(
    question,
    model="gpt-4-32k",
    stop_sequence=None,
):
    """
    Get 2-3 keywords from given question.
    """
    if question is None:
        return ""

    template = (
        "I would like to search the literature to find answer for the following question. "
        + "Give me 2 to 3 keywords that I should include in my literature search. "
        + 'List the most important keyword first and concatenate them by "+". '
        + 'Make them concise, for example: use "ABCC1" instead of "ABCC1 gene". '
        + "For example, for the question "
        + '"What is the biological rationale for an association between the gene ABCC1 and cardiotoxicity?" '
        + 'The keywords are "ABCC1+cardiotoxicity+biological rationale". '
        + "\n\nQuestion: {question}\nAnswer: "
    )

    prompt = template.format(question=question)
    try:
        return complete_model(prompt, model, stop_sequence)[0]
    except Exception as e:
        print(e)
        return ""


def trim_incomplete_sentence(paragraph):
    sentences = paragraph.split(". ")
    # if the last sentence is complete
    if sentences[-1].endswith("."):
        return paragraph
    # else, remove it
    trimmed_paragraph = ". ".join(sentences[:-1])
    trimmed_paragraph += "."
    return trimmed_paragraph


def complete_model(
    prompt,
    model,
    stop_sequence,
):

    if "gpt-4" in model:
        max_tokens = 8000
    else:
        # encoding = tiktoken.get_encoding(embedding_encoding)
        # n_tokens = len(encoding.encode(prompt))
        n_tokens = len(prompt) // 4
        max_tokens = 3880 - n_tokens

    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=stop_sequence,
        temperature=0,
        model=model,
    )

    return response.choices[0].message.content, estimate_cost(response)


def show_cost(amount):
    if amount < 0.01:
        return "< $0.01"
    else:
        return f"${amount:.2f}"
