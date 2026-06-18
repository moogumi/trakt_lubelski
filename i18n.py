#!/usr/bin/env python3
"""Localization for the waste-collection bot. Supported: en (default), ru, uk, pl."""
import os
from datetime import date, datetime

LANGS = ("en", "ru", "uk", "pl")
DEFAULT = "en"

# Language labels for the in-bot selection buttons.
LANG_NAMES = {
    "en": "English 🇬🇧",
    "ru": "Русский 🇷🇺",
    "uk": "Українська 🇺🇦",
    "pl": "Polski 🇵🇱",
}

# Meaningful category icons — language-independent.
EMOJI = {
    "OP": "📄",   # paper
    "OS": "🍾",   # glass
    "MT": "🧴",   # plastic
    "BK": "🍎",   # bio (kitchen)
    "OZ": "🌳",   # green waste
    "BG": "🍽️",   # bio (restaurant)
    "ZM": "🗑️",   # mixed
    "WG": "🛋️",   # bulky
}

# Category names keyed by id_frakcja. One word per language.
CATEGORIES = {
    "OP": {"en": "Paper",   "ru": "Бумага",      "uk": "Папір",        "pl": "Papier"},
    "OS": {"en": "Glass",   "ru": "Стекло",      "uk": "Скло",         "pl": "Szkło"},
    "MT": {"en": "Plastic", "ru": "Пластик",     "uk": "Пластик",      "pl": "Plastik"},
    "BK": {"en": "Bio",     "ru": "Био",         "uk": "Біо",          "pl": "Bio"},
    "OZ": {"en": "Green",   "ru": "Зелёные",     "uk": "Зелені",       "pl": "Zielone"},
    "BG": {"en": "Gastro",  "ru": "Гастро",      "uk": "Гастро",       "pl": "Gastro"},
    "ZM": {"en": "Mixed",   "ru": "Смешанные",   "uk": "Змішані",      "pl": "Zmieszane"},
    "WG": {"en": "Bulky",   "ru": "Габаритные",  "uk": "Габаритні",    "pl": "Gabaryty"},
}

STRINGS = {
    "title":    {"en": "Waste collection", "ru": "Вывоз мусора", "uk": "Вивіз сміття", "pl": "Wywóz odpadów"},
    "no_data":  {"en": "No schedule data.", "ru": "Нет данных в графике.", "uk": "Немає даних у графіку.", "pl": "Brak danych w harmonogramie."},
    "today":    {"en": "today", "ru": "сегодня", "uk": "сьогодні", "pl": "dzisiaj"},
    "tomorrow": {"en": "tomorrow", "ru": "завтра", "uk": "завтра", "pl": "jutro"},
    "passed":   {"en": "passed", "ru": "прошло", "uk": "минуло", "pl": "minęło"},
    "test_ok":  {
        "en": "✅ Test: TRAKT LUBELSKI 26 waste bot is configured.",
        "ru": "✅ Тест: бот вывоза мусора TRAKT LUBELSKI 26 настроен.",
        "uk": "✅ Тест: бот вивозу сміття TRAKT LUBELSKI 26 налаштований.",
        "pl": "✅ Test: bot wywozu odpadów TRAKT LUBELSKI 26 jest skonfigurowany.",
    },
    "choose_lang": {
        "en": "🌐 Choose language:",
        "ru": "🌐 Выберите язык:",
        "uk": "🌐 Оберіть мову:",
        "pl": "🌐 Wybierz język:",
    },
    "lang_set": {
        "en": "✅ Language: English",
        "ru": "✅ Язык: Русский",
        "uk": "✅ Мова: Українська",
        "pl": "✅ Język: Polski",
    },
    "welcome": {
        "en": "👋 I send the waste-collection schedule for TRAKT LUBELSKI 26.\n\n/next — schedule now\n/language — change language\n/settings — notification settings",
        "ru": "👋 Присылаю график вывоза мусора для TRAKT LUBELSKI 26.\n\n/next — график сейчас\n/language — сменить язык\n/settings — настройки уведомлений",
        "uk": "👋 Надсилаю графік вивозу сміття для TRAKT LUBELSKI 26.\n\n/next — графік зараз\n/language — змінити мову\n/settings — налаштування сповіщень",
        "pl": "👋 Wysyłam harmonogram wywozu odpadów dla TRAKT LUBELSKI 26.\n\n/next — harmonogram teraz\n/language — zmień język\n/settings — ustawienia powiadomień",
    },
    "settings_title": {"en": "⚙️ Settings", "ru": "⚙️ Настройки", "uk": "⚙️ Налаштування", "pl": "⚙️ Ustawienia"},
    "btn_schedule": {"en": "📅 Schedule", "ru": "📅 График", "uk": "📅 Графік", "pl": "📅 Harmonogram"},
    "btn_language": {"en": "🌐 Language", "ru": "🌐 Язык", "uk": "🌐 Мова", "pl": "🌐 Język"},
    "btn_settings": {"en": "⚙️ Settings", "ru": "⚙️ Настройки", "uk": "⚙️ Налаштування", "pl": "⚙️ Ustawienia"},
    "opt_scope": {"en": "Show in a notification:", "ru": "Показывать в уведомлении:", "uk": "Показувати в сповіщенні:", "pl": "Pokaż w powiadomieniu:"},
    "scope_all": {"en": "All upcoming", "ru": "Весь график", "uk": "Весь графік", "pl": "Cały harmonogram"},
    "scope_due": {"en": "Only due", "ru": "Только ближайшее", "uk": "Тільки найближче", "pl": "Tylko nadchodzące"},
    "opt_days": {"en": "Notify days before:", "ru": "Уведомлять за дней:", "uk": "Сповіщати за днів:", "pl": "Powiadom dni wcześniej:"},
    "settings_saved": {"en": "✅ Settings updated", "ru": "✅ Настройки обновлены", "uk": "✅ Налаштування оновлено", "pl": "✅ Ustawienia zaktualizowane"},
    "nothing_due": {
        "en": "✅ No collection within the next {n} day(s).",
        "ru": "✅ Ближайшие {n} дн. вывоза нет.",
        "uk": "✅ Найближчі {n} дн. вивозу немає.",
        "pl": "✅ Brak wywozu w ciągu {n} dni.",
    },
}


def norm(lang):
    lang = (lang or "").strip().lower()[:2]
    return lang if lang in LANGS else DEFAULT


# Map a tapped reply-keyboard button (in any language) to an action.
_BUTTON_ACTIONS = {
    "btn_schedule": "schedule",
    "btn_language": "language",
    "btn_settings": "settings",
}


def action_for(text):
    """Return 'schedule' | 'language' | 'settings' if text matches a button label."""
    text = (text or "").strip().lower()
    for key, action in _BUTTON_ACTIONS.items():
        if text in {v.lower() for v in STRINGS[key].values()}:
            return action
    return None


def t(key, lang):
    lang = norm(lang)
    return STRINGS[key].get(lang, STRINGS[key][DEFAULT])


def category(code, lang):
    lang = norm(lang)
    return CATEGORIES.get(code, {}).get(lang) or code


def emoji(code):
    return EMOJI.get(code, "🗑️")


def _plural_ru(n, one, few, many):
    if 11 <= n % 100 <= 14:
        return many
    last = n % 10
    if last == 1:
        return one
    if 2 <= last <= 4:
        return few
    return many


def when(days, lang):
    """Human-readable relative time for a day difference."""
    lang = norm(lang)
    if days < 0:
        return t("passed", lang)
    if days == 0:
        return t("today", lang)
    if days == 1:
        return t("tomorrow", lang)
    n = days
    if lang == "en":
        return f"in {n} days"
    if lang == "ru":
        return f"через {n} {_plural_ru(n, 'день', 'дня', 'дней')}"
    if lang == "uk":
        return f"через {n} {_plural_ru(n, 'день', 'дні', 'днів')}"
    if lang == "pl":
        return f"za {n} dni"
    return f"in {n} days"


def _days_until(d_str, today=None):
    today = today or date.today()
    return (datetime.strptime(d_str, "%Y-%m-%d").date() - today).days


def _fmt_date(d_str):
    return datetime.strptime(d_str, "%Y-%m-%d").strftime("%d.%m.%Y")


def select(schedule, scope, days_before):
    """Filter the schedule for a notification.

    scope "all"  -> the whole upcoming schedule;
    scope "due"  -> only pickups happening within `days_before` days (incl. today).
    """
    if scope != "due":
        return schedule
    return [e for e in schedule if 0 <= _days_until(e["date"]) <= int(days_before)]


def format_schedule(address, schedule, lang):
    """Build the HTML schedule message in the given language.

    schedule is a list of {date, code, ...} from waste.fetch_schedule.
    """
    lang = norm(lang)
    lines = [
        f"♻️ <b>{t('title', lang)}</b>",
        f"📍 <i>{address}</i>",
        "",
    ]
    if not schedule:
        lines.append(t("no_data", lang))
        return "\n".join(lines)
    for e in schedule:
        days = _days_until(e["date"])
        lines.append(
            f"{emoji(e['code'])} <b>{category(e['code'], lang)}</b> — "
            f"{_fmt_date(e['date'])} ({when(days, lang)})"
        )
    return "\n".join(lines)


def load_lang(cfg_path=None):
    """Read lang= from config.txt (next to the script). Defaults to en."""
    if cfg_path is None:
        cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.txt")
    if os.path.exists(cfg_path):
        with open(cfg_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("lang=") and "=" in line:
                    return norm(line.split("=", 1)[1])
    return DEFAULT
