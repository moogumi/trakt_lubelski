#!/usr/bin/env python3
"""One-shot poll + broadcast (for cron / GitHub Actions).

For the interactive bot with in-chat language/settings buttons, use bot.py.
This script just polls the site and sends the schedule to every subscriber in
their own language, filtered by their scope / days_before settings.

Usage:
  python monitor.py                 # one poll, print to console (+send if TG configured)
  python monitor.py --send          # force sending to Telegram
  python monitor.py --no-send       # console only
  python monitor.py --watch 120     # loop every 120 s (simple local mode)
  python monitor.py --log run.log   # also append a heartbeat to a file
  python monitor.py --scope due --days 1   # override scope/days for this run
                                           # (production cron: only tomorrow's pickups)
"""
import os
import sys
import time
from datetime import datetime, timezone

import config
import i18n
import store
import tg_alert
import waste

HERE = os.path.dirname(os.path.abspath(__file__))


def target_chats():
    """Subscribers from state.json; if none, fall back to the Telegram chat_id."""
    chats = store.all_chats()
    if chats:
        return chats
    tgcfg = tg_alert.load_cfg()
    return [tgcfg["chat_id"]] if tgcfg else []


def chat_defaults(cfg):
    return {
        "lang": cfg["lang"],
        "scope": cfg["notify_scope"],
        "days_before": int(cfg["notify_days_before"]),
    }


def poll(cfg, do_send, logfile=None, scope_override=None, days_override=None):
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    schedule = waste.fetch_schedule(cfg["address_point_id"])

    # console preview uses the default language and the full schedule
    print(f"[{stamp}] polled: {len(schedule)} categories")
    print(i18n.format_schedule(cfg["address"], schedule, cfg["lang"]))
    print("-" * 40)

    sent = 0
    if do_send:
        defaults = chat_defaults(cfg)
        for chat in target_chats():
            lang = store.get_opt(chat, "lang", defaults["lang"])
            scope = scope_override or store.get_opt(chat, "scope", defaults["scope"])
            days = days_override if days_override is not None else store.get_opt(chat, "days_before", defaults["days_before"])
            items = i18n.select(schedule, scope, days)
            if scope == "due" and not items:
                continue  # nothing due — stay quiet
            res = tg_alert.call("sendMessage", {
                "chat_id": chat,
                "text": i18n.format_schedule(cfg["address"], items, lang),
                "parse_mode": "HTML",
                "disable_web_page_preview": "true",
            })
            if res and res.get("ok"):
                sent += 1
        status = f"TG: sent to {sent} chat(s)"
    else:
        status = "TG: skipped (no config or --no-send)"
    print(status)

    if logfile:
        with open(logfile, "a", encoding="utf-8") as f:
            f.write(f"[{stamp}] categories={len(schedule)}  {status}\n")


def main():
    args = sys.argv[1:]
    cfg = config.load()

    watch = int(args[args.index("--watch") + 1]) if "--watch" in args else None

    logfile = None
    if "--log" in args:
        logfile = args[args.index("--log") + 1]
        if not os.path.isabs(logfile):
            logfile = os.path.join(HERE, logfile)

    if "--no-send" in args:
        do_send = False
    elif "--send" in args:
        do_send = True
    else:
        do_send = tg_alert.load_cfg() is not None

    scope_override = args[args.index("--scope") + 1] if "--scope" in args else None
    days_override = int(args[args.index("--days") + 1]) if "--days" in args else None

    if watch:
        print(f"Watching every {watch}s: '{cfg['address']}'. Ctrl-C to stop.")
        while True:
            try:
                poll(cfg, do_send, logfile, scope_override, days_override)
            except Exception as e:
                err = f"[{datetime.now(timezone.utc).isoformat(timespec='seconds')}] ERROR: {e}"
                print(err)
                if logfile:
                    with open(logfile, "a", encoding="utf-8") as f:
                        f.write(err + "\n")
            time.sleep(watch)
    else:
        poll(cfg, do_send, logfile, scope_override, days_override)


if __name__ == "__main__":
    main()
