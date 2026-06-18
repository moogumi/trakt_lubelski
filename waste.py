#!/usr/bin/env python3
"""Fetch the waste-collection schedule from warszawa19115.pl.

Uses the same Liferay portlet AJAX endpoint the site itself calls:
  1) autocompleteResource — turn a text address into an addressPointId;
  2) ajaxResource         — return the calendar (harmonogramyZ) for that id.

No third-party dependencies — stdlib only (urllib + cookiejar), siren-style.
"""
import http.cookiejar
import json
import urllib.parse
import urllib.request
from datetime import date, datetime

OC_URL = "https://warszawa19115.pl/harmonogramy-wywozu-odpadow"
PID = "portalCKMjunkschedules_WAR_portalCKMjunkschedulesportlet_INSTANCE_o5AIb2mimbRJ"

# Placeholder date meaning "not in the schedule".
NO_DATE = "1900-01-01"

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) trakt-lubelski-bot/1.0"


def _opener():
    """Opener with a cookie jar — the portal needs a session cookie between calls."""
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def _get_json(opener, params, timeout=30):
    url = OC_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": UA})
    with opener.open(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def resolve_address(address, timeout=30):
    """Address string -> list of (fullName, addressPointId). First is the best match."""
    opener = _opener()
    # warm up the session (cookie)
    opener.open(urllib.request.Request(OC_URL, headers={"User-Agent": UA}), timeout=timeout).read()
    data = _get_json(opener, {
        "p_p_id": PID,
        "p_p_lifecycle": "2",
        "p_p_resource_id": "autocompleteResource",
        f"_{PID}_name": address,
    }, timeout=timeout)
    return [(d.get("fullName", ""), d.get("addressPointId")) for d in data]


def fetch_schedule(address_point_id, timeout=30):
    """addressPointId -> list of {date, code, raw_name} dicts, sorted by date.

    `code` is id_frakcja (OP/OS/MT/...); name localization happens in the view layer.
    Entries with the 1900-01-01 placeholder (not scheduled) are dropped.
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
        raise ValueError("Unexpected API response: no harmonogramyZ")

    out = []
    for block in data:
        for e in block.get("harmonogramyZ") or []:
            d = e.get("data")
            if not d or d == NO_DATE:
                continue
            fr = e.get("frakcja") or {}
            code = fr.get("id_frakcja", "?")
            out.append({
                "date": d,
                "code": code,
                "raw_name": fr.get("nazwa", code),
            })
    out.sort(key=lambda x: x["date"])
    return out


def days_until(d_str, today=None):
    today = today or date.today()
    return (datetime.strptime(d_str, "%Y-%m-%d").date() - today).days


if __name__ == "__main__":
    import sys

    import i18n
    addr = sys.argv[1] if len(sys.argv) > 1 else "TRAKT LUBELSKI 26"
    lang = sys.argv[2] if len(sys.argv) > 2 else i18n.load_lang()
    matches = resolve_address(addr)
    print("Address matches:")
    for full, apid in matches[:5]:
        print(f"  {apid}  {full}")
    if matches:
        apid = matches[0][1]
        print(f"\nSchedule for addressPointId={apid} (lang={lang}):")
        for e in fetch_schedule(apid):
            print(f"  {e['date']}  {i18n.emoji(e['code'])} {i18n.category(e['code'], lang)}"
                  f"  ({i18n.when(days_until(e['date']), lang)})")
