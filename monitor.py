#!/usr/bin/env python3
"""Монитор графика вывоза мусора для TRAKT LUBELSKI 26 -> уведомления в Telegram.

Тестовый режим (по умолчанию): на каждой итерации опрашивает сайт и присылает
весь ближайший график по категориям — чтобы убедиться, что данные верные.

Использование:
  python monitor.py                 # один опрос, печать в консоль (+отправка, если настроен TG)
  python monitor.py --watch 120     # цикл: опрос каждые 120 сек (2 минуты)
  python monitor.py --send          # принудительно отправлять в Telegram
  python monitor.py --no-send       # никогда не отправлять (только консоль)
  python monitor.py --log run.log   # дублировать вывод в файл
"""
import os
import sys
import time
from datetime import datetime, timezone

import tg_alert
import waste

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = os.path.join(HERE, "config.txt")

DEFAULTS = {
    "address": "TRAKT LUBELSKI 26 04-870 Wawer",
    "address_point_id": "27088875",
}


def load_cfg():
    cfg = dict(DEFAULTS)
    if os.path.exists(CFG):
        with open(CFG, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip()
    return cfg


def _plural_days(n):
    n = abs(n)
    if 11 <= n % 100 <= 14:
        return "дней"
    last = n % 10
    if last == 1:
        return "день"
    if 2 <= last <= 4:
        return "дня"
    return "дней"


def human_when(days):
    if days < 0:
        return "прошло"
    if days == 0:
        return "сегодня"
    if days == 1:
        return "завтра"
    return f"через {days} {_plural_days(days)}"


def format_message(address, schedule):
    lines = [f"🗑️ <b>Вывоз мусора — {address}</b>", ""]
    if not schedule:
        lines.append("Нет данных в графике.")
        return "\n".join(lines)
    for e in schedule:
        days = waste.days_until(e["date"])
        lines.append(f"{e['emoji']} <b>{e['name']}</b>\n     {e['date']} — {human_when(days)}")
    return "\n".join(lines)


def poll(cfg, do_send, logfile=None):
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    apid = cfg["address_point_id"]
    schedule = waste.fetch_schedule(apid)
    msg = format_message(cfg["address"], schedule)

    heartbeat = f"[{stamp}] опрошено: {len(schedule)} категорий"
    print(heartbeat)
    print(msg)
    print("-" * 40)

    if do_send:
        ok, err = tg_alert.send(msg)
        status = "TG: отправлено" if ok else f"TG: ОШИБКА — {err}"
        print(status)
    else:
        status = "TG: пропущено (нет конфига или --no-send)"

    if logfile:
        with open(logfile, "a", encoding="utf-8") as f:
            f.write(heartbeat + "  " + status + "\n")


def main():
    args = sys.argv[1:]
    cfg = load_cfg()

    watch = None
    if "--watch" in args:
        watch = int(args[args.index("--watch") + 1])

    logfile = None
    if "--log" in args:
        logfile = args[args.index("--log") + 1]
        if not os.path.isabs(logfile):
            logfile = os.path.join(HERE, logfile)

    # отправлять ли в Telegram: по умолчанию — да, если конфиг настроен
    if "--no-send" in args:
        do_send = False
    elif "--send" in args:
        do_send = True
    else:
        do_send = tg_alert.load_cfg() is not None

    if watch:
        print(f"Слежу каждые {watch}с за графиком «{cfg['address']}». Ctrl-C для остановки.")
        while True:
            try:
                poll(cfg, do_send, logfile)
            except Exception as e:
                err = f"[{datetime.now(timezone.utc).isoformat(timespec='seconds')}] ОШИБКА: {e}"
                print(err)
                if logfile:
                    with open(logfile, "a", encoding="utf-8") as f:
                        f.write(err + "\n")
            time.sleep(watch)
    else:
        poll(cfg, do_send, logfile)


if __name__ == "__main__":
    main()
