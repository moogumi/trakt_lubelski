#!/usr/bin/env python3
"""Bot state in state.json: per-chat options + getUpdates offset.

Format: {"chats": {"187859119": {"lang": "ru", "scope": "all", "days_before": 1}},
         "offset": 123}
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "state.json")


def _load():
    try:
        with open(STATE, encoding="utf-8") as f:
            d = json.load(f)
    except Exception:
        d = {}
    d.setdefault("chats", {})
    d.setdefault("offset", 0)
    return d


def _save(d):
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    os.replace(tmp, STATE)


def subscribe(chat_id, defaults):
    """Ensure the chat exists, seeding any missing options from `defaults`."""
    d = _load()
    c = d["chats"].setdefault(str(chat_id), {})
    for k, v in defaults.items():
        c.setdefault(k, v)
    _save(d)


def set_opt(chat_id, key, value):
    d = _load()
    d["chats"].setdefault(str(chat_id), {})[key] = value
    _save(d)


def get_opt(chat_id, key, default=None):
    return _load()["chats"].get(str(chat_id), {}).get(key, default)


def all_chats():
    return list(_load()["chats"].keys())


def get_offset():
    return _load().get("offset", 0)


def set_offset(offset):
    d = _load()
    d["offset"] = offset
    _save(d)
