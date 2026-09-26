import asyncio

import httpx

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

MAX_RETRIES_ON_429 = 2  # up to 3 total attempts: original + 2 retries
_BACKOFF_SCHEDULE = [2.0, 4.0]  # wait before retry 1, wait before retry 2
_DEFAULT_RETRY_AFTER = 2.0


class GroqError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def _parse_retry_after(response: httpx.Response, default: float) -> float:
    raw = response.headers.get("Retry-After")
    if raw is None:
        return default
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return default
    return value if value >= 0 else default


class GroqClient:
    def __init__(self, api_key: str):
        self._api_key = api_key

    async def chat_completion(
        self,
        model: str,
        messages: list[dict],
        tools: list[dict] | None = None,
        tool_choice: str = "auto",
    ) -> dict:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        body = {"model": model, "messages": messages}
        if tools:
            body["tools"] = tools
            body["tool_choice"] = tool_choice

        async with httpx.AsyncClient() as client:
            attempt = 0
            while True:
                try:
                    response = await client.post(GROQ_URL, headers=headers, json=body, timeout=60.0)
                except httpx.RequestError as exc:
                    raise GroqError(f"Could not reach Groq: {exc}")

                if response.status_code == 429 and attempt < MAX_RETRIES_ON_429:
                    default_wait = (
                        _BACKOFF_SCHEDULE[attempt]
                        if attempt < len(_BACKOFF_SCHEDULE)
                        else _DEFAULT_RETRY_AFTER
                    )
                    wait_seconds = _parse_retry_after(response, default_wait)
                    await asyncio.sleep(wait_seconds)
                    attempt += 1
                    continue

                break

        if response.status_code == 401:
            raise GroqError("Invalid Groq API key.", status_code=401)
        if response.status_code == 402:
            raise GroqError(
                "Groq: insufficient credits on this account. Check your billing at "
                "https://console.groq.com.",
                status_code=402,
            )
        if response.status_code == 429:
            raise GroqError(
                "Groq rate limit exceeded even after retrying. This model's per-minute "
                "limit may be too low for this workload -- wait a minute and try again, "
                "or try a smaller model (e.g. openai/gpt-oss-20b).",
                status_code=429,
            )
        if response.status_code >= 400:
            detail = _extract_error_message(response)
            raise GroqError(f"Groq error: {detail}", status_code=response.status_code)

        data = response.json()
        choices = data.get("choices") or []
        if not choices:
            raise GroqError("Groq returned no choices.")
        return choices[0]["message"]


def _extract_error_message(response: httpx.Response) -> str:
    try:
        payload = response.json()
        return payload.get("error", {}).get("message", response.text[:300])
    except Exception:
        return response.text[:300]
