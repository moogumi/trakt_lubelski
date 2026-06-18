#!/usr/bin/env python3
"""Loader for config.txt (address, addressPointId, default language, interval)."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "config.txt")

DEFAULTS = {
    "address": "TRAKT LUBELSKI 26 04-870 Wawer",
    "address_point_id": "27088875",
    "lang": "en",                 # default language for new chats
    "poll_seconds": "120",        # test-broadcast interval (seconds)
    "notify_scope": "all",        # "all" upcoming or "due" (within notify_days_before)
    "notify_days_before": "1",    # consider a pickup "due" within this many days
    "reminder_time": "19:30",     # daily reminder HH:MM, Warsaw time (sent by bot.py loop)
}


def load():
    cfg = dict(DEFAULTS)
    if os.path.exists(PATH):
        with open(PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip()
    return cfg
