# Waste-collection bot — TRAKT LUBELSKI 26

Telegram bot that polls [warszawa19115.pl](https://warszawa19115.pl/harmonogramy-wywozu-odpadow)
and sends the waste-collection schedule by category for **TRAKT LUBELSKI 26 04-870 Wawer**.

No third-party dependencies — Python 3 stdlib only (modeled on the `siren` project).

## Files

| File | Purpose |
|------|---------|
| `waste.py` | Site API: address → `addressPointId` → schedule (`harmonogramyZ`). |
| `i18n.py` | Localization (en/ru/uk/pl), message formatting, schedule filtering. |
| `tg_alert.py` | Send Telegram messages (urllib, no libraries). |
| `bot.py` | Interactive bot: `/start`, `/next`, `/language`, `/settings` (+ `--push` broadcast). |
| `monitor.py` | One-shot poll + broadcast for cron / GitHub Actions. |
| `config.py` / `store.py` | Config loader and per-chat state (`state.json`). |
| `config.txt` | Address, default language and notification settings (committed). |
| `tg_config.txt` | Bot token and chat_id (gitignored). |
| `start_monitor.bat` / `stop_monitor.bat` | Start/stop the background bot on Windows. |
| `.github/workflows/poll.yml` | Cloud run via GitHub Actions (after testing). |

## Waste categories

| Code | Category | |
|------|----------|--|
| OP | Paper | 📄 |
| OS | Glass | 🍾 |
| MT | Metals & plastics | 🥫 |
| BK | Bio (kitchen) | 🍎 |
| OZ | Green waste | 🌳 |
| ZM | Mixed waste | 🗑️ |
| WG | Bulky waste | 🛋️ |

## Telegram setup

1. In Telegram message [@BotFather](https://t.me/BotFather) → `/newbot` → get the **token**.
2. Copy the template: `copy tg_config.example.txt tg_config.txt`, put in `bot_token`.
3. Send your bot any message.
4. Find `chat_id`: `python tg_alert.py` — it prints the chat_id. Put it in `tg_config.txt`.
5. Verify: `python tg_alert.py` — a test message should arrive.

## In-bot commands

- `/start`, `/help` — greeting and command list
- `/language` — pick language (EN / RU / UK / PL), saved per chat
- `/settings` — notification settings:
  - **scope**: `All upcoming` or `Only due`
  - **days before**: how many days ahead counts as "due"
- `/next` — send the full schedule right now

## Run (test mode — every 2 minutes)

```
start_monitor.bat
```

Runs `bot.py --push`: answers commands and broadcasts the schedule every 2 minutes.
Stop with `stop_monitor.bat`.

One-off poll to console (no sending):

```
python monitor.py --no-send
```

## Change address

```
python waste.py "NEW ADDRESS"
```

Take the `addressPointId` of the first match and put it in `config.txt`.

## Cloud run (after testing)

In GitHub: **Settings → Secrets and variables → Actions** add `TG_BOT_TOKEN` and `TG_CHAT_ID`.
The `poll.yml` workflow runs on a schedule (GitHub Actions: minimum every 5 minutes) and
sends to every subscriber, each in their own language and notification settings.
