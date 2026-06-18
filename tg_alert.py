#!/usr/bin/env python3
"""Отправка сообщений в Telegram — только стандартная библиотека (как в siren).

Конфиг берётся из переменных окружения TG_BOT_TOKEN / TG_CHAT_ID (для облака)
или из файла tg_config.txt рядом со скриптом (для локального запуска).

Запусти  python tg_alert.py  чтобы:
  - если chat_id не задан — увидеть chat_id всех, кто написал боту;
  - если задан — получить тестовое сообщение.
"""
import json
import os
import urllib.parse
import urllib.request

API = "https://api.telegram.org/bot{token}/{method}"
CFG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tg_config.txt")
PLACEHOLDERS = {"", "PASTE_BOT_TOKEN_HERE", "PASTE_CHAT_ID_HERE"}


def load_cfg():
    """Возвращает {'bot_token','chat_id'} или None, если не настроено."""
    token = os.environ.get("TG_BOT_TOKEN", "").strip()
    chat = os.environ.get("TG_CHAT_ID", "").strip()
    if token and chat:
        return {"bot_token": token, "chat_id": chat}

    cfg = {}
    if os.path.exists(CFG):
        with open(CFG, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip()
    token = token or cfg.get("bot_token", "")
    chat = chat or cfg.get("chat_id", "")
    if token in PLACEHOLDERS or chat in PLACEHOLDERS:
        return None
    return {"bot_token": token, "chat_id": chat}


def _api(token, method, params, timeout=30):
    url = API.format(token=token, method=method)
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def send(text, cfg=None):
    """Отправить сообщение. Возвращает (ok: bool, err: str|None)."""
    cfg = cfg or load_cfg()
    if not cfg:
        return False, "telegram не настроен (нет tg_config.txt или TG_BOT_TOKEN/TG_CHAT_ID)"
    try:
        res = _api(cfg["bot_token"], "sendMessage", {
            "chat_id": cfg["chat_id"],
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": "true",
        })
        if res.get("ok"):
            return True, None
        return False, json.dumps(res, ensure_ascii=False)
    except Exception as e:
        return False, str(e)


def _discover_chat_ids(token):
    """Печатает chat_id всех, кто недавно писал боту (через getUpdates)."""
    try:
        res = _api(token, "getUpdates", {})
    except Exception as e:
        print(f"Ошибка getUpdates: {e}")
        return
    seen = {}
    for u in res.get("result", []):
        msg = u.get("message") or u.get("edited_message") or {}
        chat = msg.get("chat") or {}
        if chat.get("id"):
            seen[chat["id"]] = chat.get("username") or chat.get("first_name") or "?"
    if not seen:
        print("Никто ещё не писал боту. Напиши боту любое сообщение и запусти снова.")
    else:
        print("Найденные chat_id (впиши нужный в tg_config.txt):")
        for cid, who in seen.items():
            print(f"  chat_id={cid}   ({who})")


if __name__ == "__main__":
    cfg = load_cfg()
    if not cfg:
        # пробуем хотя бы токен, чтобы показать chat_id
        token = os.environ.get("TG_BOT_TOKEN", "").strip()
        if not token and os.path.exists(CFG):
            with open(CFG, encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("bot_token="):
                        token = line.split("=", 1)[1].strip()
        if token and token not in PLACEHOLDERS:
            _discover_chat_ids(token)
        else:
            print("Впиши bot_token в tg_config.txt (от @BotFather) и запусти снова.")
    else:
        ok, err = send("✅ Тест: бот вывоза мусора TRAKT LUBELSKI 26 настроен.", cfg)
        print("Отправлено." if ok else f"Ошибка: {err}")
