from groq import Groq

from .config import (
    GROQ_API_KEY,
    GROQ_MODEL,
    LLM_PROVIDER,
    LLM_TEMPERATURE,
)


_client = None


def get_groq_client():
    global _client

    if not GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY is missing. Add it to backend/.env file."
        )

    if _client is None:
        _client = Groq(api_key=GROQ_API_KEY)

    return _client


def generate_llm_answer(prompt):
    """
    Non-streaming LLM answer.
    Used by document analysis, normal chat fallback, export generation, etc.
    """

    if LLM_PROVIDER != "groq":
        raise ValueError(
            f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}. Use LLM_PROVIDER=groq"
        )

    client = get_groq_client()

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=LLM_TEMPERATURE,
    )

    return response.choices[0].message.content or ""


def stream_llm_answer(prompt):
    """
    Streaming LLM answer.
    Used by /chat-stream/ endpoint.
    """

    if LLM_PROVIDER != "groq":
        raise ValueError(
            f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}. Use LLM_PROVIDER=groq"
        )

    client = get_groq_client()

    stream = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=LLM_TEMPERATURE,
        stream=True,
    )

    for chunk in stream:
        if not chunk.choices:
            continue

        delta = chunk.choices[0].delta

        if delta and delta.content:
            yield delta.content


def generate_llm_answer_stream(prompt):
    return stream_llm_answer(prompt)


def stream_llm_tokens(prompt):
    return stream_llm_answer(prompt)


def warmup_llm():
    return {
        "status": "ready",
        "provider": LLM_PROVIDER,
        "model": GROQ_MODEL,
        "message": "Groq does not require local warmup.",
    }