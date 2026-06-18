#!/usr/bin/env python3
"""Interactive Telegram bot for TRAKT LUBELSKI 26 waste collection.

Commands:
  /start, /help        — greeting and command list
  /language, /lang     — pick language with buttons (EN / RU / UK / PL)
  /settings            — notification settings (scope + days-before)
  /next, /schedule     — send the full schedule now (in the chat's language)

Per-chat settings (stored in state.json):
  lang         — message language
  scope        — "all" (whole schedule) or "due" (only pickups within days_before)
  days_before  — how many days ahead counts as "due"

Run:
  python bot.py            # interactive only (answers commands)
  python bot.py --push     # interactive + test broadcast to all subscribers
                           #   every poll_seconds (config.txt, default 120 s),
                           #   filtered per chat by scope/days_before
"""
import json
import os
import sys
import time

import config
import i18n
import store
import tg_alert
import waste

DAY_OPTIONS = (1, 2, 3, 4, 5, 6, 7)


def chat_defaults(cfg):
    return {
        "lang": cfg["lang"],
        "scope": cfg["notify_scope"],
        "days_before": int(cfg["notify_days_before"]),
    }


def opt(chat, key, cfg):
    return store.get_opt(chat, key, chat_defaults(cfg)[key])


# ---------- keyboards ----------

def main_keyboard(lang):
    """Persistent reply keyboard shown at the bottom of the chat."""
    return {
        "keyboard": [
            [{"text": i18n.t("btn_schedule", lang)}],
            [{"text": i18n.t("btn_language", lang)}, {"text": i18n.t("btn_settings", lang)}],
        ],
        "resize_keyboard": True,
    }


def lang_keyboard():
    btns = [{"text": name, "callback_data": "setlang:" + code}
            for code, name in i18n.LANG_NAMES.items()]
    return {"inline_keyboard": [btns[:2], btns[2:]]}  # 2x2


def settings_keyboard(lang, scope, days):
    def mark(text, on):
        return ("✅ " if on else "") + text

    row_scope = [
        {"text": mark(i18n.t("scope_all", lang), scope == "all"), "callback_data": "setscope:all"},
        {"text": mark(i18n.t("scope_due", lang), scope == "due"), "callback_data": "setscope:due"},
    ]
    row_days = [
        {"text": mark(str(d), int(days) == d), "callback_data": f"setdays:{d}"}
        for d in DAY_OPTIONS
    ]
    return {"inline_keyboard": [row_scope, row_days]}


def settings_text(lang, scope, days):
    scope_label = i18n.t("scope_all" if scope == "all" else "scope_due", lang)
    return (
        f"<b>{i18n.t('settings_title', lang)}</b>\n\n"
        f"{i18n.t('opt_scope', lang)} <b>{scope_label}</b>\n"
        f"{i18n.t('opt_days', lang)} <b>{days}</b>"
    )


# ---------- rendering ----------

def full_schedule_text(cfg, lang):
    sched = waste.fetch_schedule(cfg["address_point_id"])
    return i18n.format_schedule(cfg["address"], sched, lang)


def notification_text(cfg, lang, scope, days):
    """Filtered text for an automatic notification, or None if nothing is due."""
    sched = waste.fetch_schedule(cfg["address_point_id"])
    items = i18n.select(sched, scope, days)
    if scope == "due" and not items:
        return None
    return i18n.format_schedule(cfg["address"], items, lang)


# ---------- telegram helpers ----------

def send(tg, chat_id, text, reply_markup=None):
    params = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    }
    if reply_markup:
        params["reply_markup"] = json.dumps(reply_markup)
    return tg("sendMessage", params)


def edit(tg, chat_id, message_id, text, reply_markup=None):
    params = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML",
    }
    if reply_markup:
        params["reply_markup"] = json.dumps(reply_markup)
    return tg("editMessageText", params)


# ---------- update handling ----------

def handle_callback(cq, cfg, tg):
    data = cq.get("data", "")
    chat = cq["message"]["chat"]["id"]
    mid = cq["message"]["message_id"]
    store.subscribe(chat, chat_defaults(cfg))
    lang = opt(chat, "lang", cfg)

    if data.startswith("setlang:"):
        code = i18n.norm(data.split(":", 1)[1])
        store.set_opt(chat, "lang", code)
        tg("answerCallbackQuery", {"callback_query_id": cq["id"]})
        send(tg, chat, i18n.t("lang_set", code), reply_markup=main_keyboard(code))
        send(tg, chat, full_schedule_text(cfg, code))

    elif data.startswith("setscope:"):
        store.set_opt(chat, "scope", data.split(":", 1)[1])
        _refresh_settings(tg, chat, mid, cfg, lang, cq["id"])

    elif data.startswith("setdays:"):
        store.set_opt(chat, "days_before", int(data.split(":", 1)[1]))
        _refresh_settings(tg, chat, mid, cfg, lang, cq["id"])


def _refresh_settings(tg, chat, mid, cfg, lang, cq_id):
    scope = opt(chat, "scope", cfg)
    days = opt(chat, "days_before", cfg)
    tg("answerCallbackQuery", {"callback_query_id": cq_id, "text": i18n.t("settings_saved", lang)})
    edit(tg, chat, mid, settings_text(lang, scope, days), settings_keyboard(lang, scope, days))


def handle_message(msg, cfg, tg):
    chat = (msg.get("chat") or {}).get("id")
    if not chat:
        return
    store.subscribe(chat, chat_defaults(cfg))
    lang = opt(chat, "lang", cfg)
    raw = (msg.get("text") or "").strip()
    text = raw.lower()
    action = i18n.action_for(raw)  # tapped reply-keyboard button (any language)

    if text.startswith("/start"):
        send(tg, chat, i18n.t("welcome", lang), reply_markup=main_keyboard(lang))
        send(tg, chat, i18n.t("choose_lang", lang), reply_markup=lang_keyboard())
    elif action == "language" or text.startswith("/lang") or text.startswith("/language"):
        send(tg, chat, i18n.t("choose_lang", lang), reply_markup=lang_keyboard())
    elif action == "settings" or text.startswith("/settings"):
        scope = opt(chat, "scope", cfg)
        days = opt(chat, "days_before", cfg)
        send(tg, chat, settings_text(lang, scope, days), reply_markup=settings_keyboard(lang, scope, days))
    elif action == "schedule" or text.startswith("/next") or text.startswith("/schedule"):
        send(tg, chat, full_schedule_text(cfg, lang), reply_markup=main_keyboard(lang))
    else:  # /help and any other text
        send(tg, chat, i18n.t("welcome", lang), reply_markup=main_keyboard(lang))


def handle_update(u, cfg, tg):
    cq = u.get("callback_query")
    if cq:
        handle_callback(cq, cfg, tg)
        return
    msg = u.get("message")
    if msg:
        handle_message(msg, cfg, tg)


# ---------- broadcast ----------

def push_all(cfg, tg):
    sched = waste.fetch_schedule(cfg["address_point_id"])
    chats = store.all_chats()
    if not chats:
        tgcfg = tg_alert.load_cfg()
        chats = [tgcfg["chat_id"]] if tgcfg else []
    sent = 0
    for chat in chats:
        lang = opt(chat, "lang", cfg)
        scope = opt(chat, "scope", cfg)
        days = opt(chat, "days_before", cfg)
        items = i18n.select(sched, scope, days)
        if scope == "due" and not items:
            continue  # nothing due — stay quiet
        send(tg, chat, i18n.format_schedule(cfg["address"], items, lang))
        sent += 1
    return sent


# ---------- main loop ----------

def main():
    cfg = config.load()
    tgcfg = tg_alert.load_cfg()
    if not tgcfg:
        print("Telegram not configured (no tg_config.txt or TG_BOT_TOKEN/TG_CHAT_ID).")
        sys.exit(1)

    def tg(method, params):
        try:
            return tg_alert.call(method, params, tgcfg)
        except Exception as e:
            print(f"TG {method} error: {e}")
            return None

    # populate the "/" menu in Telegram clients
    tg("setMyCommands", {"commands": json.dumps([
        {"command": "next", "description": "Schedule / Harmonogram"},
        {"command": "language", "description": "Language / Język"},
        {"command": "settings", "description": "Notifications / Powiadomienia"},
    ])})

    # --once: drain pending updates once and exit (for GitHub Actions polling)
    if "--once" in sys.argv:
        offset = store.get_offset()
        res = tg("getUpdates", {"offset": offset, "timeout": 0})
        n = 0
        for u in (res or {}).get("result", []):
            offset = u["update_id"] + 1
            store.set_offset(offset)
            try:
                handle_update(u, cfg, tg)
                n += 1
            except Exception as e:
                print(f"handle error: {e}")
        print(f"[once] processed {n} update(s)")
        return

    do_push = "--push" in sys.argv
    interval = int(cfg.get("poll_seconds", "120"))

    # LOOP_MINUTES > 0: long-running mode for GitHub Actions — exit after N
    # minutes so the scheduled job ends and cron can restart it (near-continuous
    # coverage via a concurrency lock). 0 = run forever (local).
    loop_min = float(os.environ.get("LOOP_MINUTES", "0"))
    deadline = (time.time() + loop_min * 60) if loop_min > 0 else None
    print(f"Bot started. Commands: /start /next /language /settings."
          f" Broadcast: {'every ' + str(interval) + 's' if do_push else 'off'}."
          f" Deadline: {str(int(loop_min)) + ' min' if deadline else 'none'}.")

    offset = store.get_offset()
    last_push = 0.0
    while True:
        try:
            res = tg("getUpdates", {"offset": offset, "timeout": 25})
            for u in (res or {}).get("result", []):
                offset = u["update_id"] + 1
                store.set_offset(offset)
                try:
                    handle_update(u, cfg, tg)
                except Exception as e:
                    print(f"handle error: {e}")
        except Exception as e:
            print(f"loop error: {e}")
            time.sleep(3)

        if do_push and time.time() - last_push >= interval:
            last_push = time.time()
            try:
                n = push_all(cfg, tg)
                print(f"[push] sent to {n} chat(s)")
            except Exception as e:
                print(f"push error: {e}")

        if deadline and time.time() >= deadline:
            print("loop deadline reached — exiting for restart")
            break


if __name__ == "__main__":
    main()
