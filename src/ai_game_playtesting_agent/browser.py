from pathlib import Path

from playwright.sync_api import Browser, Page, Playwright, TimeoutError, sync_playwright

from ai_game_playtesting_agent.config import Settings
from ai_game_playtesting_agent.models import Move

KEY_MAP: dict[Move, str] = {
    "up": "ArrowUp",
    "down": "ArrowDown",
    "left": "ArrowLeft",
    "right": "ArrowRight",
}


class GameBrowser:
    """Thin Playwright wrapper for 2048."""

    def __init__(self, settings: Settings, headed: bool = False):
        self.settings = settings
        self.headed = headed
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self.page: Page | None = None

    def start(self) -> None:
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=not self.headed)
        self.page = self._browser.new_page(
            viewport={"width": self.settings.viewport_width, "height": self.settings.viewport_height}
        )
        self.page.goto(self.settings.game_url, wait_until="domcontentloaded")
        self.page.wait_for_timeout(self.settings.page_load_timeout_ms)
        self.dismiss_welcome_tooltip()

    def dismiss_welcome_tooltip(self) -> bool:
        """Close the play2048.co welcome banner so score and board are visible."""
        assert self.page is not None
        tooltip = self.page.locator(".tooltip-material").filter(has_text="Welcome to 2048")
        try:
            tooltip.first.wait_for(state="visible", timeout=self.settings.page_load_timeout_ms)
        except TimeoutError:
            return False

        close_button = tooltip.locator("button.rounded-full")
        close_button.first.click()
        tooltip.first.wait_for(state="hidden", timeout=self.settings.page_load_timeout_ms)
        self.page.wait_for_timeout(self.settings.animation_ms)
        return True

    def screenshot(self, path: Path) -> None:
        assert self.page is not None
        path.parent.mkdir(parents=True, exist_ok=True)
        self.page.screenshot(
            path=str(path),
            type="jpeg",
            quality=self.settings.screenshot_jpeg_quality,
            full_page=False,
        )

    def press_move(self, move: Move) -> None:
        assert self.page is not None
        if move == "restart":
            self.restart()
            return
        key = KEY_MAP[move]
        self.page.keyboard.press(key)
        self.page.wait_for_timeout(self.settings.animation_ms)

    def restart(self) -> None:
        assert self.page is not None
        for selector in (
            "text=Try again",
            ".retry-button",
            "a.restart-button",
        ):
            locator = self.page.locator(selector)
            if locator.count() > 0:
                locator.first.click()
                self.page.wait_for_timeout(self.settings.animation_ms)
                return
        self.page.reload(wait_until="domcontentloaded")
        self.page.wait_for_timeout(self.settings.page_load_timeout_ms)
        self.dismiss_welcome_tooltip()

    def close(self) -> None:
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
        self.page = None
        self._browser = None
        self._playwright = None
