#!/usr/bin/env python3
"""Send Telegram messages — stdlib only (siren-style).

Config comes from env vars TG_BOT_TOKEN / TG_CHAT_ID (for the cloud) or from
tg_config.txt next to the script (for local runs).

Run  python tg_alert.py  to:
  - if chat_id is not set — print the chat_id of everyone who messaged the bot;
  - if it is set — send a test message.
"""
import json
import os
import urllib.parse
import urllib.request

API = "https://api.telegram.org/bot{token}/{method}"
CFG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tg_config.txt")
PLACEHOLDERS = {"", "PASTE_BOT_TOKEN_HERE", "PASTE_CHAT_ID_HERE"}


def load_cfg():
    """Return {'bot_token', 'chat_id'} or None if not configured."""
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


def _api(token, method, params, timeout=40):
    url = API.format(token=token, method=method)
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def call(method, params, cfg=None, timeout=40):
    """Low-level Bot API call. Returns parsed JSON, or None if not configured."""
    cfg = cfg or load_cfg()
    if not cfg:
        return None
    return _api(cfg["bot_token"], method, params, timeout=timeout)


def send(text, cfg=None):
    """Send a message. Returns (ok: bool, err: str|None)."""
    cfg = cfg or load_cfg()
    if not cfg:
        return False, "telegram not configured (no tg_config.txt or TG_BOT_TOKEN/TG_CHAT_ID)"
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
    """Print the chat_id of everyone who recently messaged the bot (via getUpdates)."""
    try:
        res = _api(token, "getUpdates", {})
    except Exception as e:
        print(f"getUpdates error: {e}")
        return
    seen = {}
    for u in res.get("result", []):
        msg = u.get("message") or u.get("edited_message") or {}
        chat = msg.get("chat") or {}
        if chat.get("id"):
            seen[chat["id"]] = chat.get("username") or chat.get("first_name") or "?"
    if not seen:
        print("Nobody has messaged the bot yet. Send it any message and run again.")
    else:
        print("Found chat_id(s) (put the right one in tg_config.txt):")
        for cid, who in seen.items():
            print(f"  chat_id={cid}   ({who})")


if __name__ == "__main__":
    cfg = load_cfg()
    if not cfg:
        # try at least the token so we can print chat_id
        token = os.environ.get("TG_BOT_TOKEN", "").strip()
        if not token and os.path.exists(CFG):
            with open(CFG, encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("bot_token="):
                        token = line.split("=", 1)[1].strip()
        if token and token not in PLACEHOLDERS:
            _discover_chat_ids(token)
        else:
            print("Put bot_token in tg_config.txt (from @BotFather) and run again.")
    else:
        import i18n
        ok, err = send(i18n.t("test_ok", i18n.load_lang()), cfg)
        print("Sent." if ok else f"Error: {err}")
