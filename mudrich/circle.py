"""
This was coded based on the ANSI implementation of Dragon Ball Advent Truth, I'm not sure if it represents all of CircleMUD
"""

import re
import random

from rich.text import Text
from rich.ansi import AnsiDecoder

DEFAULT_COLORS = {
    "0": "0",      # Normal
    "1": "0;36",   # Roomname
    "2": "0;32",   # Roomobjs
    "3": "0;33",   # Roompeople
    "4": "0;31",   # Hityou
    "5": "0;32",   # Youhit
    "6": "0;33",   # Otherhit
    "7": "1;33",   # Critical
    "8": "1;33",   # Holler
    "9": "1;33",   # Shout
    "10": "0;33",  # Gossip
    "11": "0;36",  # Auction
    "12": "0;32",  # Congrat
    "13": "0;31",  # Tell
    "14": "0;36",  # Yousay
    "15": "0:37"   # Roomsay
}

COLOR_MAP = {
    "n": "0",

    "d": "0;30",
    "b": "0;34",
    "g": "0;32",
    "c": "0;36",
    "r": "0;31",
    "m": "0;35",
    "y": "0;33",
    "w": "0;37",

    "D": "1;30",
    "B": "1;34",
    "G": "1;32",
    "C": "1;36",
    "R": "1;31",
    "M": "1;35",
    "Y": "1;33",
    "W": "1;37",

    "0": "40",
    "1": "44",
    "2": "42",
    "3": "46",
    "4": "41",
    "5": "45",
    "6": "43",
    "7": "47",

    "l": "5",
    "u": "4",
    "o": "1",
    "e": "7"
}

RANDOM_CODES = ["b", "g", "c", "r", "m", "y", "w", "B", "G", "C", "R", "M", "W", "Y"]

RE_COLOR = re.compile(r"@(n|d|D|b|B|g|G|c|C|r|R|m|M|y|Y|w|W|x|0|1|2|3|4|5|6|7|l|o|u|e|@|\[\d+\])")


def CircleStrip(entry: str) -> str:

    def replace_color(match_obj):
        m = match_obj.group(1)
        match m:
            case "@":
                return "@"
            case _:
                return ""

    return RE_COLOR.sub(replace_color, entry)


def CircleToRich(entry: str, colors: dict = None) -> Text:

    custom_colors = DEFAULT_COLORS.copy()
    if colors:
        custom_colors.update(colors)

    def replace_color(match_obj):
        m = match_obj.group(1)
        match m:
            case "@":
                return "@"
            case "x":
                code = random.choice(RANDOM_CODES)
                ansi_codes = COLOR_MAP[code]
            case _:
                if m.startswith("["):
                    code = m[1:][:-1]
                    if code in custom_colors:
                        ansi_codes = custom_colors[code]
                    else:
                        return m.group(0)
                else:
                    ansi_codes = COLOR_MAP[m]
        return f"\x1b[{ansi_codes}m"

    out_text = RE_COLOR.sub(replace_color, entry)

    return AnsiDecoder().decode_line(out_text)


DEFAULT_EVMAP = {
    "0": "|n",  # Normal

    "1": "|C",  # Roomname
    "2": "|G",  # Roomobjs
    "3": "|Y",  # Roompeople
    "4": "|R",  # Hityou
    "5": "|G",  # Youhit
    "6": "|Y",  # Otherhit
    "7": "|y",  # Critical
    "8": "|y",  # Holler
    "9": "|y",  # Shout
    "10": "|Y",  # Gossip
    "11": "|C",  # Auction
    "12": "|G",  # Congrat
    "13": "|R",  # Tell
    "14": "|C",  # Yousay
    "15": "|W"  # Roomsay
}

COLOR_MAP_EV = {
    "n": "|n",

    "d": "|X",
    "b": "|B",
    "g": "|G",
    "c": "|C",
    "r": "|R",
    "m": "|M",
    "y": "|Y",
    "w": "|W",

    "D": "|x",
    "B": "|b",
    "G": "|g",
    "C": "|c",
    "R": "|r",
    "M": "|m",
    "Y": "|y",
    "W": "|w",

    "0": "|[X",
    "1": "|[B",
    "2": "|[G",
    "3": "|[C",
    "4": "|[R",
    "5": "|[M",
    "6": "|[Y",
    "7": "|[W",

    "l": "|^",
    "u": "|u",
    "o": "|h",
    "e": "|*"
}


def CircleToEvennia(entry: str) -> str:

    custom_colors = DEFAULT_EVMAP.copy()

    def replace_color(match_obj):
        m = match_obj.group(1)
        match m:
            case "@":
                return "||"
            case "x":
                code = random.choice(RANDOM_CODES)
                ansi_codes = COLOR_MAP_EV[code]
            case _:
                if m.startswith("["):
                    code = m[1:][:-1]
                    if code in custom_colors:
                        ansi_codes = custom_colors[code]
                    else:
                        return m.group(0)
                else:
                    ansi_codes = COLOR_MAP_EV[m]
        return f"{ansi_codes}"

    return RE_COLOR.sub(replace_color, entry)
