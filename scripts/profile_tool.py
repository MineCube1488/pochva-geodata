#!/usr/bin/env python3
"""Validate and stamp the Happ routing profile before it reaches clients.

check  Every geosite:/geoip: category the profile references must exist in the
       given geosite.dat / geoip.dat. Otherwise Xray on the client refuses to
       start ("failed to check code STEAM from geosite.dat > EOF", shown in
       Happ as "Ошибка запуска ядра: EOF").

stamp  Write the profile with LastUpdated. Happ re-downloads geo files only
       when LastUpdated grows (and at most once a week), so it is bumped
       whenever the profile content changes and kept as-is otherwise.

No dependencies: .dat files are protobuf lists of {1: code, 2: entries},
parsed here with a minimal wire-format reader.
"""
import argparse
import json
import sys
import time

SITE_FIELDS = ("DirectSites", "ProxySites", "BlockSites")
IP_FIELDS = ("DirectIp", "ProxyIp", "BlockIp")


def _varint(buf, i):
    result = shift = 0
    while True:
        byte = buf[i]
        i += 1
        result |= (byte & 0x7F) << shift
        shift += 7
        if byte < 0x80:
            return result, i


def _fields(buf):
    i = 0
    while i < len(buf):
        key, i = _varint(buf, i)
        num, wire = key >> 3, key & 7
        if wire == 0:
            value, i = _varint(buf, i)
        elif wire == 2:
            length, i = _varint(buf, i)
            value, i = buf[i:i + length], i + length
        elif wire == 5:
            value, i = buf[i:i + 4], i + 4
        elif wire == 1:
            value, i = buf[i:i + 8], i + 8
        else:
            raise ValueError(f"unsupported protobuf wire type {wire}")
        yield num, value


def dat_codes(path):
    """Category codes (upper-case, as Xray matches them) in a geoip/geosite .dat."""
    with open(path, "rb") as f:
        data = f.read()
    codes = set()
    for num, entry in _fields(data):
        if num != 1:
            continue
        for field, value in _fields(entry):
            if field == 1:
                codes.add(value.decode().upper())
                break
    return codes


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def cmd_check(args):
    profile = load(args.profile)
    available = {"geosite": dat_codes(args.geosite), "geoip": dat_codes(args.geoip)}
    errors = []
    checked = 0

    for field in SITE_FIELDS + IP_FIELDS:
        expected = "geosite" if field in SITE_FIELDS else "geoip"
        for rule in profile.get(field, []):
            kind, sep, rest = rule.partition(":")
            if not sep or kind not in ("geosite", "geoip"):
                continue  # domain:, full:, CIDRs, ext: files — nothing to look up
            if kind != expected:
                errors.append(f"{field}: '{rule}' — {kind}-правило в списке для {expected}")
                continue
            # geoip:!ru negates, geosite:google@cn filters by attribute
            code = rest.lstrip("!").split("@", 1)[0].upper()
            checked += 1
            if code not in available[kind]:
                errors.append(
                    f"{field}: '{rule}' — категории {code} нет в {kind}.dat "
                    f"(есть: {', '.join(sorted(available[kind]))})"
                )

    if errors:
        for error in errors:
            print(f"::error file={args.profile}::{error}")
        print(f"{len(errors)} ошибк(и) — профиль не опубликован.", file=sys.stderr)
        sys.exit(1)
    print(f"OK: все {checked} geo-категорий профиля есть в {args.geosite} и {args.geoip}")


def cmd_stamp(args):
    profile = load(args.profile)
    own_stamp = profile.pop("LastUpdated", None)

    previous = None
    if args.previous:
        try:
            previous = load(args.previous)
        except FileNotFoundError:
            pass
    prev_stamp = previous.pop("LastUpdated", None) if previous else None

    if previous is None and own_stamp:
        # First publication: clients already have this value, don't trigger a re-download wave
        stamp = own_stamp
        print(f"Первая публикация — берём LastUpdated из профиля: {stamp}")
    elif previous == profile and prev_stamp:
        stamp = prev_stamp
        print(f"Профиль не изменился — LastUpdated остаётся {stamp}")
    else:
        now = int(time.time())
        stamp = str(max(now, int(prev_stamp) + 1) if prev_stamp else now)
        print(f"Профиль изменился — LastUpdated {prev_stamp} -> {stamp}")

    # Keep LastUpdated right after Name, where Happ's own examples put it
    out = {}
    if "Name" in profile:
        out["Name"] = profile.pop("Name")
    out["LastUpdated"] = stamp
    out.update(profile)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    check = sub.add_parser("check", help="сверить категории профиля с .dat-файлами")
    check.add_argument("profile")
    check.add_argument("--geosite", required=True)
    check.add_argument("--geoip", required=True)
    check.set_defaults(func=cmd_check)

    stamp = sub.add_parser("stamp", help="записать профиль с актуальным LastUpdated")
    stamp.add_argument("profile")
    stamp.add_argument("--previous", help="опубликованный профиль (если есть)")
    stamp.add_argument("--out", required=True)
    stamp.set_defaults(func=cmd_stamp)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
