from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import yaml


@dataclass
class ReplyTemplate:
    name: str
    match_any: List[str]
    response: str


def load_templates(path: str) -> List[ReplyTemplate]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    templates: List[ReplyTemplate] = []
    for item in data.get("templates", []):
        templates.append(
            ReplyTemplate(
                name=item.get("name", "noname"),
                match_any=item.get("match_any", []),
                response=item.get("response", ""),
            )
        )
    return templates


def choose_reply(templates: List[ReplyTemplate], message_text: str) -> Optional[ReplyTemplate]:
    lower_text = (message_text or "").lower()
    for tpl in templates:
        if any(keyword.lower() in lower_text for keyword in tpl.match_any):
            return tpl
    return None

