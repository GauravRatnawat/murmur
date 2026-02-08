"""Multi-provider LLM support with lazy imports."""

import os


def _call_anthropic(system_prompt: str, user_message: str) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")
    message = client.messages.create(
        model=model,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    return message.content[0].text


def _call_openai(system_prompt: str, user_message: str) -> str:
    import openai

    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )
    return response.choices[0].message.content


def _call_gemini(system_prompt: str, user_message: str) -> str:
    import google.generativeai as genai

    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel(
        os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
        system_instruction=system_prompt,
    )
    response = model.generate_content(user_message)
    return response.text


def _call_groq(system_prompt: str, user_message: str) -> str:
    from groq import Groq

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )
    return response.choices[0].message.content


def _call_ollama(system_prompt: str, user_message: str) -> str:
    import ollama

    model = os.getenv("OLLAMA_MODEL", "llama3.2")
    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )
    return response["message"]["content"]


# Maps provider name -> (function, required_env_var or None, pip_package)
PROVIDERS = {
    "anthropic": (_call_anthropic, "ANTHROPIC_API_KEY", "anthropic"),
    "openai": (_call_openai, "OPENAI_API_KEY", "openai"),
    "gemini": (_call_gemini, "GEMINI_API_KEY", "google-generativeai"),
    "groq": (_call_groq, "GROQ_API_KEY", "groq"),
    "ollama": (_call_ollama, None, "ollama"),
}


def call_llm(provider: str, system_prompt: str, user_message: str) -> str:
    """Call an LLM provider by name. Raises RuntimeError on misconfiguration."""
    provider = provider.lower()
    if provider not in PROVIDERS:
        names = ", ".join(PROVIDERS)
        raise RuntimeError(f"Unknown provider '{provider}'. Choose from: {names}")

    func, env_var, pip_package = PROVIDERS[provider]

    if env_var and not os.getenv(env_var):
        raise RuntimeError(f"{env_var} not set. Add it to your .env file.")

    try:
        return func(system_prompt, user_message)
    except ImportError:
        raise RuntimeError(
            f"SDK for '{provider}' not installed. "
            f"Run: pip install {pip_package}"
        )
