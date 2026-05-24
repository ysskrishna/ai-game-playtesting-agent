import base64
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from ai_game_playtesting_agent.config import Settings
from ai_game_playtesting_agent.models import BoardObservation, Move

SYSTEM_PROMPT = """You are playtesting the browser game 2048 from a screenshot.

Read ONLY the image. Return structured data:
- grid: 4x4 integers (0 = empty)
- score, best_tile from the UI if visible (else estimate from grid)
- game_over: true if a Game Over overlay/message is visible
- won_2048: true if a 2048 tile exists or a win banner is shown
- move: one of up, down, left, right. Use restart ONLY when game_over is true.
- reasoning: one short sentence for your chosen move

Pick a legal move that tries to merge tiles and keep the board playable. Prefer keeping the largest tile in a corner.

Only choose a direction if tiles would slide or merge in that direction."""


def _blocked_moves_hint(blocked_moves: list[Move]) -> str:
    directions = ", ".join(blocked_moves)
    return (
        f"The last action(s) did not change the board. Do NOT choose: {directions}. "
        "Pick a different direction that will slide or merge tiles."
    )


class VisionObserver:
    def __init__(self, settings: Settings):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=settings.vision_temperature,
        ).with_structured_output(BoardObservation)

    def observe(
        self,
        screenshot_path: Path,
        blocked_moves: list[Move] | None = None,
    ) -> BoardObservation:
        image_b64 = base64.standard_b64encode(screenshot_path.read_bytes()).decode()
        user_text = "Analyze this 2048 board and choose the next move."
        if blocked_moves:
            user_text = f"{user_text}\n\n{_blocked_moves_hint(blocked_moves)}"

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=[
                    {"type": "text", "text": user_text},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                    },
                ]
            ),
        ]
        return self.llm.invoke(messages)
