# Бот вывоза мусора — TRAKT LUBELSKI 26

Telegram-бот, который опрашивает [warszawa19115.pl](https://warszawa19115.pl/harmonogramy-wywozu-odpadow)
и присылает график вывоза мусора по категориям для адреса **TRAKT LUBELSKI 26 04-870 Wawer**.

Без внешних зависимостей — только стандартная библиотека Python 3 (стиль проекта `siren`).

## Файлы

| Файл | Назначение |
|------|-----------|
| `waste.py` | Запрос к API сайта: адрес → `addressPointId` → график (`harmonogramyZ`). |
| `tg_alert.py` | Отправка сообщений в Telegram (urllib, без библиотек). |
| `monitor.py` | Главный цикл: опрос → форматирование → отправка. |
| `config.txt` | Адрес и `address_point_id` (закоммичен, не секрет). |
| `tg_config.txt` | Токен бота и `chat_id` (в `.gitignore`). |
| `start_monitor.bat` / `stop_monitor.bat` | Запуск/остановка фонового монитора на Windows. |
| `.github/workflows/poll.yml` | Облачный запуск через GitHub Actions (после теста). |

## Категории мусора

| Код | Категория | |
|-----|-----------|--|
| OP | Папир (бумага/картон) | 🟦 |
| OS | Стекло | 🟩 |
| MT | Металл и пластик | 🟨 |
| BK | Био (кухонные отходы) | 🟫 |
| OZ | Зелёные отходы | 🌿 |
| ZM | Смешанные отходы | ⬛ |
| WG | Крупногабаритные | 🛋️ |

## Настройка Telegram

1. В Telegram напиши [@BotFather](https://t.me/BotFather) → `/newbot` → получи **токен**.
2. Скопируй шаблон: `copy tg_config.example.txt tg_config.txt`, впиши `bot_token`.
3. Напиши своему боту любое сообщение.
4. Узнай `chat_id`: `python tg_alert.py` — он напечатает chat_id. Впиши его в `tg_config.txt`.
5. Проверка: `python tg_alert.py` — должно прийти тестовое сообщение.

## Запуск (тестовый режим — каждые 2 минуты)

```
start_monitor.bat
```

Каждые 2 минуты бот опрашивает сайт и присылает весь ближайший график. Остановить — `stop_monitor.bat`.

Разовый опрос в консоль (без отправки):

```
python monitor.py --no-send
```

## Смена адреса

```
python waste.py "НОВЫЙ АДРЕС"
```

Взять `addressPointId` первого совпадения и вписать в `config.txt`.

## Облачный запуск (после теста)

В GitHub: **Settings → Secrets and variables → Actions** добавить `TG_BOT_TOKEN` и `TG_CHAT_ID`.
Workflow `poll.yml` запускается по расписанию (GitHub Actions: минимум каждые 5 минут).
