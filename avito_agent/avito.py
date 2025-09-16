from __future__ import annotations

import json
import os
import random
import time
from dataclasses import dataclass
from typing import List, Optional

from playwright.sync_api import BrowserContext, Page, sync_playwright


@dataclass
class Dialog:
    dialog_id: str
    title: str
    last_message_preview: str
    unread: bool


class AvitoClient:
    def __init__(self, headless: bool = True, cookies_path: Optional[str] = None):
        self.headless = headless
        self.cookies_path = cookies_path
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    def __enter__(self) -> "AvitoClient":
        self._p = sync_playwright().start()
        browser = self._p.chromium.launch(headless=self.headless)
        context = browser.new_context()
        self._context = context
        if self.cookies_path and os.path.exists(self.cookies_path):
            with open(self.cookies_path, "r", encoding="utf-8") as f:
                cookies = json.load(f)
            context.add_cookies(cookies)
        self._page = context.new_page()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if self.cookies_path and self._context is not None:
                try:
                    os.makedirs(os.path.dirname(self.cookies_path), exist_ok=True)
                    cookies = self._context.cookies()
                    with open(self.cookies_path, "w", encoding="utf-8") as f:
                        json.dump(cookies, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass
        finally:
            if self._context is not None:
                self._context.close()
            if hasattr(self, "_p") and self._p is not None:
                self._p.stop()

    @property
    def page(self) -> Page:
        assert self._page is not None, "Page not initialized"
        return self._page

    def login(self, login: str, password: str) -> None:
        self.page.goto("https://www.avito.ru/profile/login", wait_until="domcontentloaded")
        # Avito может редиректить на unified auth, подбираем селекторы осторожно
        # Пытаемся ввести логин
        if self.page.locator("input[type=email], input[name=email], input[name=login]").first.is_visible():
            field = self.page.locator("input[type=email], input[name=email], input[name=login]").first
            field.fill(login)
            self.page.keyboard.press("Enter")
        else:
            # Телефон
            phone_field = self.page.locator("input[type=tel], input[name=phone]").first
            phone_field.fill(login)
            self.page.keyboard.press("Enter")

        # Ждем поле пароля
        self.page.wait_for_selector("input[type=password], input[name=password]")
        self.page.locator("input[type=password], input[name=password]").first.fill(password)
        self.page.keyboard.press("Enter")

        # Ждем появления UI профиля
        self.page.wait_for_url(lambda url: "profile" in url or "messenger" in url, timeout=60000)

    def go_to_messages(self) -> None:
        self.page.goto("https://www.avito.ru/messenger", wait_until="domcontentloaded")
        self.page.wait_for_selector('[data-marker="messenger"]', timeout=60000)

    def list_dialogs(self) -> List[Dialog]:
        dialogs: List[Dialog] = []
        items = self.page.locator('[data-marker="messenger/dialogs/list"] [data-marker="dialog-item"]')
        count = items.count()
        for i in range(count):
            item = items.nth(i)
            dialog_id = item.get_attribute("data-id") or str(i)
            title = item.locator('[data-marker="dialog/title"]').inner_text(timeout=5000)
            preview = item.locator('[data-marker="dialog/preview"]').inner_text(timeout=5000)
            unread = item.locator('[data-marker="dialog/unread"]').count() > 0
            dialogs.append(Dialog(dialog_id=dialog_id, title=title, last_message_preview=preview, unread=unread))
        return dialogs

    def open_dialog(self, dialog: Dialog) -> None:
        self.page.locator(f'[data-marker="dialog-item"][data-id="{dialog.dialog_id}"]').click()
        self.page.wait_for_selector('[data-marker="message-list"]', timeout=30000)

    def read_last_message(self) -> str:
        messages = self.page.locator('[data-marker="message-list"] [data-marker="message-text"]')
        count = messages.count()
        if count == 0:
            return ""
        return messages.nth(count - 1).inner_text()

    def send_reply(self, text: str, actually_send: bool = True) -> None:
        input_box = self.page.locator('textarea, [contenteditable="true"]').first
        input_box.click()
        input_box.fill(text)
        if actually_send:
            # Ищем кнопку отправки
            send_button = self.page.locator('[data-marker="send-button"], button[type=submit]')
            if send_button.count() > 0:
                send_button.first.click()
            else:
                self.page.keyboard.press("Enter")

    @staticmethod
    def human_delay(min_s: int, max_s: int) -> None:
        time.sleep(random.uniform(min_s, max_s))

