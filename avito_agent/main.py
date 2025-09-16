from __future__ import annotations

import argparse
import os
import sys
from dotenv import load_dotenv

from avito_agent.config import load_settings
from avito_agent.avito import AvitoClient
from avito_agent.templates import load_templates, choose_reply


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Avito Auto-Reply Agent")
    parser.add_argument("--only-unread", action="store_true", help="Обрабатывать только непрочитанные диалоги")
    parser.add_argument("--templates", default="templates/replies.yaml", help="Путь к YAML с шаблонами")
    parser.add_argument("--dry-run", action="store_true", help="Сухой прогон без отправки")
    parser.add_argument("--label", default=None, help="Метка/префикс в сообщении для отслеживания")
    return parser.parse_args()


def main() -> int:
    load_dotenv()
    args = parse_args()
    settings = load_settings()
    if args.dry_run:
        settings.dry_run = True

    templates = load_templates(args.templates)

    with AvitoClient(headless=settings.headless, cookies_path=settings.cookies_path) as client:
        # Если нет cookies, пробуем логин
        if not os.path.exists(settings.cookies_path):
            if not settings.avito_login or not settings.avito_password:
                print("Не заданы AVITO_LOGIN/AVITO_PASSWORD и отсутствуют cookies. Отмена.")
                return 1
            client.login(settings.avito_login, settings.avito_password)

        client.go_to_messages()
        dialogs = client.list_dialogs()
        handled = 0

        for dialog in dialogs:
            if args.only_unread and not dialog.unread:
                continue
            if handled >= settings.max_replies_per_run:
                break

            client.open_dialog(dialog)
            AvitoClient.human_delay(settings.min_delay_s, settings.max_delay_s)
            last_text = client.read_last_message()
            tpl = choose_reply(templates, last_text)
            if not tpl:
                continue

            message = tpl.response
            if args.label:
                message = f"[{args.label}]\n" + message

            print(f"Ответ в диалоге {dialog.dialog_id} — шаблон: {tpl.name}")
            if settings.dry_run:
                print("DRY-RUN: ")
                print(message)
            else:
                client.send_reply(message, actually_send=True)

            handled += 1
            AvitoClient.human_delay(settings.min_delay_s, settings.max_delay_s)

    print(f"Готово. Обработано диалогов: {handled}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

