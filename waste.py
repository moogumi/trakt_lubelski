#!/usr/bin/env python3
"""Получение графика вывоза мусора с warszawa19115.pl.

Работает по той же AJAX-ручке портала Liferay, что использует сам сайт:
  1) autocompleteResource — превращает текстовый адрес в addressPointId;
  2) ajaxResource         — по addressPointId отдаёт календарь (harmonogramyZ).

Без внешних зависимостей — только стандартная библиотека (urllib + cookiejar),
в стиле проекта siren.
"""
import http.cookiejar
import json
import urllib.parse
import urllib.request
from datetime import date, datetime

OC_URL = "https://warszawa19115.pl/harmonogramy-wywozu-odpadow"
PID = "portalCKMjunkschedules_WAR_portalCKMjunkschedulesportlet_INSTANCE_o5AIb2mimbRJ"

# id_frakcja -> (человекочитаемое имя, эмодзи / цвет контейнера)
FRAKCJE = {
    "OP": ("Папир (бумага/картон)", "🟦"),
    "OS": ("Стекло", "🟩"),
    "MT": ("Металл и пластик", "🟨"),
    "BK": ("Био (кухонные отходы)", "🟫"),
    "OZ": ("Зелёные отходы", "🌿"),
    "BG": ("Био (ресторанное)", "🍽️"),
    "ZM": ("Смешанные отходы", "⬛"),
    "WG": ("Крупногабаритные", "🛋️"),
}

# Дата-заглушка «нет в графике» в ответе API.
NO_DATE = "1900-01-01"

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) trakt-lubelski-bot/1.0"


def _opener():
    """Opener с хранилищем cookie — портал требует session-cookie между запросами."""
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def _get_json(opener, params, timeout=30):
    url = OC_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": UA})
    with opener.open(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def resolve_address(address, timeout=30):
    """Адрес-строка -> список (fullName, addressPointId). Первый — самый релевантный."""
    opener = _opener()
    # прогреваем сессию (cookie)
    opener.open(urllib.request.Request(OC_URL, headers={"User-Agent": UA}), timeout=timeout).read()
    data = _get_json(opener, {
        "p_p_id": PID,
        "p_p_lifecycle": "2",
        "p_p_resource_id": "autocompleteResource",
        f"_{PID}_name": address,
    }, timeout=timeout)
    return [(d.get("fullName", ""), d.get("addressPointId")) for d in data]


def fetch_schedule(address_point_id, timeout=30):
    """addressPointId -> список словарей {date, id, name, emoji}, отсортированный по дате.

    Записи с датой-заглушкой 1900-01-01 (нет в графике) отбрасываются.
    """
    opener = _opener()
    opener.open(urllib.request.Request(OC_URL, headers={"User-Agent": UA}), timeout=timeout).read()
    data = _get_json(opener, {
        "p_p_id": PID,
        "p_p_lifecycle": "2",
        "p_p_resource_id": "ajaxResource",
        f"_{PID}_addressPointId": str(address_point_id),
    }, timeout=timeout)

    if not data or "harmonogramyZ" not in data[0]:
        raise ValueError("Неожиданный ответ API: нет harmonogramyZ")

    out = []
    for block in data:
        for e in block.get("harmonogramyZ") or []:
            d = e.get("data")
            if not d or d == NO_DATE:
                continue
            fr = e.get("frakcja") or {}
            code = fr.get("id_frakcja", "?")
            name, emoji = FRAKCJE.get(code, (fr.get("nazwa", code), "🗑️"))
            out.append({
                "date": d,
                "code": code,
                "name": name,
                "emoji": emoji,
            })
    out.sort(key=lambda x: x["date"])
    return out


def days_until(d_str, today=None):
    today = today or date.today()
    return (datetime.strptime(d_str, "%Y-%m-%d").date() - today).days


if __name__ == "__main__":
    import sys
    addr = sys.argv[1] if len(sys.argv) > 1 else "TRAKT LUBELSKI 26"
    matches = resolve_address(addr)
    print("Совпадения адреса:")
    for full, apid in matches[:5]:
        print(f"  {apid}  {full}")
    if matches:
        apid = matches[0][1]
        print(f"\nГрафик для addressPointId={apid}:")
        for e in fetch_schedule(apid):
            print(f"  {e['date']}  {e['emoji']} {e['name']}  (через {days_until(e['date'])} дн.)")
