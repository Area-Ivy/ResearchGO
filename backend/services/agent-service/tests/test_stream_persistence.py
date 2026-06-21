import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.api.agent import AgentChatRequest, agent_chat
from app.models.state import StreamEvent


class DummyRequest:
    def __init__(self, token="test-token"):
        self.headers = {"Authorization": f"Bearer {token}"}


class DummyCache:
    def __init__(self):
        self.saved_messages = []

    async def append_message(self, conversation_id, role, content, token):
        self.saved_messages.append(
            {
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "token": token,
            }
        )


class DummyAgent:
    async def run_stream(self, **kwargs):
        yield StreamEvent(event="token", data="Hello")
        yield StreamEvent(event="token", data=" world")
        yield StreamEvent(event="answer_end", data=None)
        yield StreamEvent(event="done", data=None)


@pytest.mark.asyncio
async def test_streaming_tokens_are_persisted(monkeypatch):
    cache = DummyCache()

    monkeypatch.setattr("app.api.agent.get_conversation_cache", lambda: cache)
    monkeypatch.setattr("app.api.agent.get_agent", lambda: DummyAgent())

    response = await agent_chat(
        AgentChatRequest(message="hi", conversation_id=123, stream=True),
        DummyRequest(),
        current_user={"user_id": "u1"},
    )

    body = response.body_iterator
    async for _ in body:
        pass

    assert cache.saved_messages[-1] == {
        "conversation_id": 123,
        "role": "assistant",
        "content": "Hello world",
        "token": "test-token",
    }
