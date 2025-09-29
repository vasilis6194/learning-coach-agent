"""Root agent configuration for the Learning Coach project."""

from __future__ import annotations

import asyncio
import sys

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


import json
import os
import uuid
from typing import Any, Optional

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types

try:
    from .subagents.summarizer.agent import SummarizerAgent
except ImportError:
    from subagents.summarizer.agent import SummarizerAgent

load_dotenv()



# --- Constants ---
_DEFAULT_MODEL = "gemini-2.0-flash"


def _get_model_name() -> str:
    """Resolve the root agent's model name from env or fallback."""
    return (
        os.getenv("ROOT_AGENT_MODEL")
        or os.getenv("GEMINI_MODEL")
        or _DEFAULT_MODEL
    )


def build_root_agent(model_name: Optional[str] = None) -> Agent:
    """Create a fresh root agent wired to the summarizer (only for now)."""
    summarizer = SummarizerAgent.model_copy(deep=False)

    return Agent(
        name="LearningCoachRoot",
        model=model_name or _get_model_name(),
        description="Root agent that orchestrates learning-coach sub-agents.",
        instruction="""
You are the Learning Coach root agent.

For now, you only have **SummarizerAgent** available:
- Call the tool `transfer_to_agent` with {"agent_name": "SummarizerAgent"} whenever the learner asks for summaries, notes, key takeaways, or document conversions.
- Do not emit JSON or prose in those cases—use the actual function call so the handoff happens.
- If the request is outside summarization, politely explain that summarization is the only supported capability right now.

Later you will also gain:
- QuizAgent (to generate practice questions)
- FlashcardAgent (to create spaced-repetition flashcards)
""",

        sub_agents=[summarizer],
    )


# --- Global entrypoints (picked up by ADK) ---
RootAgent = build_root_agent()
root_agent = RootAgent


def build_runner(
    *,
    app_name: str = "LearningCoach",
    fresh_agent: bool = True,
) -> InMemoryRunner:
    """Create an InMemoryRunner for local testing."""
    agent = build_root_agent() if fresh_agent else RootAgent
    return InMemoryRunner(agent=agent, app_name=app_name)


def run_summary(
    text: str,
    *,
    app_name: str = "LearningCoach",
    user_id: str = "test-user",
    session_id: Optional[str] = None,
    fresh_agent: bool = True,
) -> dict[str, Any]:
    """Run the root agent against SummarizerAgent for quick local tests."""
    runner = build_runner(app_name=app_name, fresh_agent=fresh_agent)

    content = types.Content(
        role="user",
        parts=[types.Part.from_text(text=text)],
    )

    session_identifier = session_id or str(uuid.uuid4())
    final_event = None
    for event in runner.run(
        user_id=user_id,
        session_id=session_identifier,
        new_message=content,
    ):
        final_event = event

    if not final_event or not final_event.content:
        return {}

    payload = "".join(part.text or "" for part in final_event.content.parts).strip()
    if not payload:
        return {}

    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return {"raw": payload}


__all__ = [
    "RootAgent",
    "build_root_agent",
    "build_runner",
    "run_summary",
    "root_agent",
]
