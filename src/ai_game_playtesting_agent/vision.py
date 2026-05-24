import base64
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from ai_game_playtesting_agent.config import Settings
from ai_game_playtesting_agent.models import BoardObservation

SYSTEM_PROMPT = """You are playtesting the browser game 2048 from a screenshot.

Read ONLY the image. Return structured data:
- grid: 4x4 integers (0 = empty)
- score, best_tile from the UI if visible (else estimate from grid)
- game_over: true if a Game Over overlay/message is visible
- won_2048: true if a 2048 tile exists or a win banner is shown
- move: one of up, down, left, right. Use restart ONLY when game_over is true.
- reasoning: one short sentence for your chosen move
- confidence: high, medium, or low

Pick a legal move that tries to merge tiles and keep the board playable. Prefer keeping the largest tile in a corner."""


class VisionObserver:
    def __init__(self, settings: Settings):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0,
        ).with_structured_output(BoardObservation)

    def observe(self, screenshot_path: Path) -> BoardObservation:
        image_b64 = base64.standard_b64encode(screenshot_path.read_bytes()).decode()
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=[
                    {"type": "text", "text": "Analyze this 2048 board and choose the next move."},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                    },
                ]
            ),
        ]
        return self.llm.invoke(messages)
