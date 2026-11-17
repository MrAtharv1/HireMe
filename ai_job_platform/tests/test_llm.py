import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pydantic import BaseModel, Field

from app.services.llm import (
    extract_json_object,
    LLMProvider,
    GroqProvider,
    GeminiProvider,
    get_llm_provider,
)


class SampleSchema(BaseModel):
    name: str
    score: int = Field(ge=0, le=100)
    skills: list[str]


def test_extract_json_clean():
    raw = '{"name": "Alice", "score": 95, "skills": ["Python", "SQL"]}'
    res = extract_json_object(raw)
    assert res["name"] == "Alice"
    assert res["score"] == 95
    assert len(res["skills"]) == 2


def test_extract_json_markdown_and_trailing_commas():
    raw = """
    Here is the response:
    ```json
    {
        "name": "Bob",
        "score": 80,
        "skills": ["FastAPI", "Docker",],
    }
    ```
    Thank you!
    """
    res = extract_json_object(raw)
    assert res["name"] == "Bob"
    assert res["score"] == 80
    assert res["skills"] == ["FastAPI", "Docker"]


@pytest.mark.asyncio
async def test_groq_provider_validation_retry():
    provider = GroqProvider(api_key="gsk_mock_test_key", model="openai/gpt-oss-120b")

    # First attempt returns invalid schema (missing 'skills')
    # Second attempt returns valid schema
    invalid_resp = MagicMock()
    invalid_resp.choices = [MagicMock(message=MagicMock(content='{"name": "Carol", "score": 75}'))]
    invalid_resp.usage = MagicMock(prompt_tokens=10, completion_tokens=10, total_tokens=20)

    valid_resp = MagicMock()
    valid_resp.choices = [MagicMock(message=MagicMock(content='{"name": "Carol", "score": 75, "skills": ["React"]}'))]
    valid_resp.usage = MagicMock(prompt_tokens=15, completion_tokens=15, total_tokens=30)

    with patch("groq.AsyncGroq") as mock_groq_cls:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=[invalid_resp, valid_resp])
        mock_groq_cls.return_value = mock_client

        res = await provider.complete_json(
            system="System instruction",
            user="Generate Carol",
            json_schema=SampleSchema,
        )

        assert res["name"] == "Carol"
        assert res["score"] == 75
        assert res["skills"] == ["React"]
        assert mock_client.chat.completions.create.call_count == 2


def test_get_llm_provider_factory():
    provider = get_llm_provider()
    assert isinstance(provider, LLMProvider)
