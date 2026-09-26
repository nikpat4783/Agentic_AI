from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx

from app.agent.groq_client import GROQ_URL, GroqClient, GroqError

MESSAGES = [{"role": "user", "content": "hello"}]


def _completion_response(content: str = "hi there") -> httpx.Response:
    return httpx.Response(
        200,
        json={"choices": [{"message": {"role": "assistant", "content": content}}]},
    )


def _rate_limit_response(retry_after: str | None = None) -> httpx.Response:
    headers = {"Retry-After": retry_after} if retry_after else {}
    return httpx.Response(429, json={"error": {"message": "rate limited"}}, headers=headers)


@pytest.mark.asyncio
@respx.mock
async def test_429_then_200_succeeds_on_retry():
    respx.post(GROQ_URL).mock(
        side_effect=[_rate_limit_response(), _completion_response("survived retry")]
    )

    with patch("app.agent.groq_client.asyncio.sleep", new=AsyncMock()) as mock_sleep:
        client = GroqClient("fake-key")
        message = await client.chat_completion("openai/gpt-oss-120b", MESSAGES)

    assert message == {"role": "assistant", "content": "survived retry"}
    mock_sleep.assert_awaited_once()


@pytest.mark.asyncio
@respx.mock
async def test_429_on_every_attempt_raises_after_exhausting_retries():
    respx.post(GROQ_URL).mock(
        side_effect=[_rate_limit_response(), _rate_limit_response(), _rate_limit_response()]
    )

    with patch("app.agent.groq_client.asyncio.sleep", new=AsyncMock()) as mock_sleep:
        client = GroqClient("fake-key")
        with pytest.raises(GroqError) as exc_info:
            await client.chat_completion("openai/gpt-oss-120b", MESSAGES)

    assert exc_info.value.status_code == 429
    assert "rate limit exceeded even after retrying" in str(exc_info.value)
    assert mock_sleep.await_count == 2  # retried twice, then gave up on the 3rd 429


@pytest.mark.asyncio
@respx.mock
async def test_402_raises_immediately_without_retry():
    respx.post(GROQ_URL).mock(
        return_value=httpx.Response(402, json={"error": {"message": "insufficient credits"}})
    )

    with patch("app.agent.groq_client.asyncio.sleep", new=AsyncMock()) as mock_sleep:
        client = GroqClient("fake-key")
        with pytest.raises(GroqError) as exc_info:
            await client.chat_completion("openai/gpt-oss-120b", MESSAGES)

    assert exc_info.value.status_code == 402
    assert "insufficient credits" in str(exc_info.value)
    assert "console.groq.com" in str(exc_info.value)
    mock_sleep.assert_not_awaited()


@pytest.mark.asyncio
@respx.mock
async def test_retry_after_header_is_respected():
    respx.post(GROQ_URL).mock(
        side_effect=[_rate_limit_response(retry_after="7"), _completion_response()]
    )

    with patch("app.agent.groq_client.asyncio.sleep", new=AsyncMock()) as mock_sleep:
        client = GroqClient("fake-key")
        await client.chat_completion("openai/gpt-oss-120b", MESSAGES)

    mock_sleep.assert_awaited_once_with(7.0)


@pytest.mark.asyncio
@respx.mock
async def test_retry_after_missing_falls_back_to_fixed_schedule():
    respx.post(GROQ_URL).mock(
        side_effect=[_rate_limit_response(), _completion_response()]
    )

    with patch("app.agent.groq_client.asyncio.sleep", new=AsyncMock()) as mock_sleep:
        client = GroqClient("fake-key")
        await client.chat_completion("openai/gpt-oss-120b", MESSAGES)

    mock_sleep.assert_awaited_once_with(2.0)
