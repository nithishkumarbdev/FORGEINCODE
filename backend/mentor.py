from anthropic import Anthropic, APIConnectionError, RateLimitError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from config import get_settings

settings = get_settings()
_client: Anthropic | None = None

MENTOR_SYSTEM = (
    "You are a patient mentor helping someone learn software development, "
    "cloud/DevOps, or security by doing real exercises themselves. They are "
    "stuck on a specific exercise, or have a question about it. Give a hint "
    "that helps them think through it - point at the concept, the specific "
    "line, or the kind of mistake they're likely making. Do NOT write the "
    "complete corrected code or solution for them, and do not simply repeat "
    "the instructions back. Keep it to 2-4 sentences."
)


def get_client() -> Anthropic:
    global _client
    if _client is None:
        if not settings.anthropic_api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Copy backend/.env.example to "
                "backend/.env and add your key from console.anthropic.com"
            )
        _client = Anthropic(api_key=settings.anthropic_api_key)
    return _client


@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type((APIConnectionError, RateLimitError)),
)
def ask_mentor(step_title: str, instructions: str, submitted: str, question: str, last_result: str | None) -> str:
    context = (
        f"Exercise: {step_title}\n\nInstructions:\n{instructions}\n\n"
        f"Their current answer:\n{submitted or '(nothing submitted yet)'}\n\n"
    )
    if last_result:
        context += f"Result of their last check:\n{last_result}\n\n"
    context += f"Their question: {question}"

    message = get_client().messages.create(
        model="claude-sonnet-5",
        max_tokens=300,
        system=MENTOR_SYSTEM,
        messages=[{"role": "user", "content": context}],
    )
    return "".join(block.text for block in message.content if block.type == "text")
