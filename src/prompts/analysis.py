"""Versioned prompt templates for article analysis."""

SYSTEM_PROMPT = (
    "You are an assistant helping a Singapore-based general insurance broker "
    "identify business opportunities from news articles. "
    "You must always respond with valid JSON only — no markdown, no explanation."
)


def build_user_prompt(title: str, article_text: str) -> str:
    """Return the user-turn prompt for article analysis."""
    safe_text = article_text[:3000].replace("{", "{{").replace("}", "}}")
    return (
        f"Analyze the following news article and respond with JSON only.\n\n"
        f'Title: "{title}"\n\n'
        f"Article text:\n{safe_text}\n\n"
        "Return exactly this JSON structure (no markdown fences, no extra keys):\n"
        "{\n"
        '  "summary": "<one sentence, 30 words or fewer, summarising the article>",\n'
        '  "companies": "<comma-separated company names mentioned in the article, or \'None identified\'>",\n'
        '  "angle": "<30 words or fewer: how a Singapore general insurance broker can open a conversation with the identified company based on this news>"\n'
        "}"
    )
