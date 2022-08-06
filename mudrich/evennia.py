"""
Evennia's ANSI code, yanked pretty much straight from it.

ANSI - Gives colour to text.

Use the codes defined in ANSIPARSER in your text to apply colour to text
according to the ANSI standard.

Examples:

```python
"This is |rRed text|n and this is normal again."
```

Mostly you should not need to call `parse_ansi()` explicitly; it is run by
Evennia just before returning data to/from the user. Depreciated example forms
are available by extending the ansi mapping.

"""
import functools
import logging

from rich.text import Text
from rich.ansi import AnsiDecoder

import re
from collections import OrderedDict

ENCODINGS = ["utf-8", "latin-1", "ISO-8859-1"]



def to_str(text, session=None):
    """
    Try to decode a bytestream to a python str, using encoding schemas from settings
    or from Session. Will always return a str(), also if not given a str/bytes.
    Args:
        text (any): The text to encode to bytes. If a str, return it. If also not bytes, convert
            to str using str() or repr() as a fallback.
        session (Session, optional): A Session to get encoding info from. Will try this before
            falling back to settings.ENCODINGS.
    Returns:
        decoded_text (str): The decoded text.
    Note:
        If `text` is already str, return it as is.
    """
    if isinstance(text, str):
        return text
    if not isinstance(text, bytes):
        # not a byte, convert directly to str
        try:
            return str(text)
        except Exception:
            return repr(text)

    default_encoding = session.protocol_flags.get("ENCODING", "utf-8") if session else "utf-8"
    try:
        return text.decode(default_encoding)
    except (LookupError, UnicodeDecodeError):
        for encoding in ENCODINGS:
            try:
                return text.decode(encoding)
            except (LookupError, UnicodeDecodeError):
                pass
        # no valid encoding found. Replace unconvertable parts with ?
        return text.decode(default_encoding, errors="replace")

# ANSI definitions

ANSI_BEEP = "\07"
ANSI_ESCAPE = "\033"
ANSI_NORMAL = "\033[0m"

ANSI_UNDERLINE = "\033[4m"
ANSI_HILITE = "\033[1m"
ANSI_UNHILITE = "\033[22m"
ANSI_BLINK = "\033[5m"
ANSI_INVERSE = "\033[7m"
ANSI_INV_HILITE = "\033[1;7m"
ANSI_INV_BLINK = "\033[7;5m"
ANSI_BLINK_HILITE = "\033[1;5m"
ANSI_INV_BLINK_HILITE = "\033[1;5;7m"

# Foreground colors
ANSI_BLACK = "\033[30m"
ANSI_RED = "\033[31m"
ANSI_GREEN = "\033[32m"
ANSI_YELLOW = "\033[33m"
ANSI_BLUE = "\033[34m"
ANSI_MAGENTA = "\033[35m"
ANSI_CYAN = "\033[36m"
ANSI_WHITE = "\033[37m"

# Background colors
ANSI_BACK_BLACK = "\033[40m"
ANSI_BACK_RED = "\033[41m"
ANSI_BACK_GREEN = "\033[42m"
ANSI_BACK_YELLOW = "\033[43m"
ANSI_BACK_BLUE = "\033[44m"
ANSI_BACK_MAGENTA = "\033[45m"
ANSI_BACK_CYAN = "\033[46m"
ANSI_BACK_WHITE = "\033[47m"

# Formatting Characters
ANSI_RETURN = "\r\n"
ANSI_TAB = "\t"
ANSI_SPACE = " "

# Escapes
ANSI_ESCAPES = ("{{", "\\\\", "\|\|")

_PARSE_CACHE = OrderedDict()
_PARSE_CACHE_SIZE = 10000

COLOR_NO_DEFAULT = False

COLOR_ANSI_EXTRA_MAP = []
# Extend the available regexes for adding XTERM256 colors in-game. This is given
# as a list of regexes, where each regex must contain three anonymous groups for
# holding integers 0-5 for the red, green and blue components Default is
# is r'\|([0-5])([0-5])([0-5])', which allows e.g. |500 for red.
# Note that to apply all color changes, a full `evennia reboot` is needed!
COLOR_ANSI_EXTRA_MAP = []
# XTERM256 foreground color replacement
# Note that to apply all color changes, a full `evennia reboot` is needed!
COLOR_XTERM256_EXTRA_FG = []
# XTERM256 background color replacement. Default is \|\[([0-5])([0-5])([0-5])'
# Note that to apply all color changes, a full `evennia reboot` is needed!
COLOR_XTERM256_EXTRA_BG = []
# Extend the available regexes for adding XTERM256 grayscale values in-game. Given
# as a list of regexes, where each regex must contain one anonymous group containing
# a single letter a-z to mark the level from white to black. Default is r'\|=([a-z])',
# which allows e.g. |=k for a medium gray.
# XTERM256 grayscale foreground
# Note that to apply all color changes, a full `evennia reboot` is needed!
COLOR_XTERM256_EXTRA_GFG = []
# XTERM256 grayscale background. Default is \|\[=([a-z])'
# Note that to apply all color changes, a full `evennia reboot` is needed!
COLOR_XTERM256_EXTRA_GBG = []
# ANSI does not support bright backgrounds, so Evennia fakes this by mapping it to
# XTERM256 backgrounds where supported. This is a list of tuples that maps the wanted
# ansi tag (not a regex!) to a valid XTERM256 tag, such as `(r'|o', r'|531')`
# for orange. By default this is only used for bright backgrounds but
# both bright and dark colors can be mapped this way, and is a way to add
# new shortcuts to xterm colors without having to write the RGB value.
# Note that to apply all color changes, a full `evennia reboot` is needed!
COLOR_ANSI_XTERM256_BRIGHT_BG_EXTRA_MAP = []


class ANSIParser(object):
    """
    A class that parses ANSI markup to ANSI command sequences.

    We also allow to escape colour codes by prepending with an extra `|`.

    """

    # Mapping using {r {n etc

    ansi_map = [
        # alternative |-format
        (r"|n", ANSI_NORMAL),  # reset
        (r"|/", ANSI_RETURN),  # line break
        (r"|-", ANSI_TAB),  # tab
        (r"|>", ANSI_SPACE * 4),  # indent (4 spaces)
        (r"|_", ANSI_SPACE),  # space
        (r"|*", ANSI_INVERSE),  # invert
        (r"|^", ANSI_BLINK),  # blinking text (very annoying and not supported by all clients)
        (r"|u", ANSI_UNDERLINE),  # underline
        (r"|r", ANSI_HILITE + ANSI_RED),
        (r"|g", ANSI_HILITE + ANSI_GREEN),
        (r"|y", ANSI_HILITE + ANSI_YELLOW),
        (r"|b", ANSI_HILITE + ANSI_BLUE),
        (r"|m", ANSI_HILITE + ANSI_MAGENTA),
        (r"|c", ANSI_HILITE + ANSI_CYAN),
        (r"|w", ANSI_HILITE + ANSI_WHITE),  # pure white
        (r"|x", ANSI_HILITE + ANSI_BLACK),  # dark grey
        (r"|R", ANSI_UNHILITE + ANSI_RED),
        (r"|G", ANSI_UNHILITE + ANSI_GREEN),
        (r"|Y", ANSI_UNHILITE + ANSI_YELLOW),
        (r"|B", ANSI_UNHILITE + ANSI_BLUE),
        (r"|M", ANSI_UNHILITE + ANSI_MAGENTA),
        (r"|C", ANSI_UNHILITE + ANSI_CYAN),
        (r"|W", ANSI_UNHILITE + ANSI_WHITE),  # light grey
        (r"|X", ANSI_UNHILITE + ANSI_BLACK),  # pure black
        # hilight-able colors
        (r"|h", ANSI_HILITE),
        (r"|H", ANSI_UNHILITE),
        (r"|!R", ANSI_RED),
        (r"|!G", ANSI_GREEN),
        (r"|!Y", ANSI_YELLOW),
        (r"|!B", ANSI_BLUE),
        (r"|!M", ANSI_MAGENTA),
        (r"|!C", ANSI_CYAN),
        (r"|!W", ANSI_WHITE),  # light grey
        (r"|!X", ANSI_BLACK),  # pure black
        # normal ANSI backgrounds
        (r"|[R", ANSI_BACK_RED),
        (r"|[G", ANSI_BACK_GREEN),
        (r"|[Y", ANSI_BACK_YELLOW),
        (r"|[B", ANSI_BACK_BLUE),
        (r"|[M", ANSI_BACK_MAGENTA),
        (r"|[C", ANSI_BACK_CYAN),
        (r"|[W", ANSI_BACK_WHITE),  # light grey background
        (r"|[X", ANSI_BACK_BLACK),  # pure black background
    ]

    ansi_xterm256_bright_bg_map = [
        # "bright" ANSI backgrounds using xterm256 since ANSI
        # standard does not support it (will
        # fallback to dark ANSI background colors if xterm256
        # is not supported by client)
        # |-style variations
        (r"|[r", r"|[500"),
        (r"|[g", r"|[050"),
        (r"|[y", r"|[550"),
        (r"|[b", r"|[005"),
        (r"|[m", r"|[505"),
        (r"|[c", r"|[055"),
        (r"|[w", r"|[555"),  # white background
        (r"|[x", r"|[222"),
    ]  # dark grey background

    # xterm256. These are replaced directly by
    # the sub_xterm256 method

    if COLOR_NO_DEFAULT:
        ansi_map = COLOR_ANSI_EXTRA_MAP
        xterm256_fg = COLOR_XTERM256_EXTRA_FG
        xterm256_bg = COLOR_XTERM256_EXTRA_BG
        xterm256_gfg = COLOR_XTERM256_EXTRA_GFG
        xterm256_gbg = COLOR_XTERM256_EXTRA_GBG
        ansi_xterm256_bright_bg_map = COLOR_ANSI_XTERM256_BRIGHT_BG_EXTRA_MAP
    else:
        xterm256_fg = [r"\|([0-5])([0-5])([0-5])"]  # |123 - foreground colour
        xterm256_bg = [r"\|\[([0-5])([0-5])([0-5])"]  # |[123 - background colour
        xterm256_gfg = [r"\|=([a-z])"]  # |=a - greyscale foreground
        xterm256_gbg = [r"\|\[=([a-z])"]  # |[=a - greyscale background
        ansi_map += COLOR_ANSI_EXTRA_MAP
        xterm256_fg += COLOR_XTERM256_EXTRA_FG
        xterm256_bg += COLOR_XTERM256_EXTRA_BG
        xterm256_gfg += COLOR_XTERM256_EXTRA_GFG
        xterm256_gbg += COLOR_XTERM256_EXTRA_GBG
        ansi_xterm256_bright_bg_map += COLOR_ANSI_XTERM256_BRIGHT_BG_EXTRA_MAP

    mxp_re = r"\|lc(.*?)\|lt(.*?)\|le"

    # prepare regex matching
    brightbg_sub = re.compile(
        r"|".join([r"(?<!\|)%s" % re.escape(tup[0]) for tup in ansi_xterm256_bright_bg_map]),
        re.DOTALL,
    )
    xterm256_fg_sub = re.compile(r"|".join(xterm256_fg), re.DOTALL)
    xterm256_bg_sub = re.compile(r"|".join(xterm256_bg), re.DOTALL)
    xterm256_gfg_sub = re.compile(r"|".join(xterm256_gfg), re.DOTALL)
    xterm256_gbg_sub = re.compile(r"|".join(xterm256_gbg), re.DOTALL)

    # xterm256_sub = re.compile(r"|".join([tup[0] for tup in xterm256_map]), re.DOTALL)
    ansi_sub = re.compile(r"|".join([re.escape(tup[0]) for tup in ansi_map]), re.DOTALL)
    mxp_sub = re.compile(mxp_re, re.DOTALL)

    # used by regex replacer to correctly map ansi sequences
    ansi_map_dict = dict(ansi_map)
    ansi_xterm256_bright_bg_map_dict = dict(ansi_xterm256_bright_bg_map)

    # prepare matching ansi codes overall
    ansi_re = r"\033\[[0-9;]+m"
    ansi_regex = re.compile(ansi_re)

    # escapes - these double-chars will be replaced with a single
    # instance of each
    ansi_escapes = re.compile(r"(%s)" % "|".join(ANSI_ESCAPES), re.DOTALL)

    def sub_ansi(self, ansimatch):
        """
        Replacer used by `re.sub` to replace ANSI
        markers with correct ANSI sequences

        Args:
            ansimatch (re.matchobject): The match.

        Returns:
            processed (str): The processed match string.

        """
        return self.ansi_map_dict.get(ansimatch.group(), "")

    def sub_brightbg(self, ansimatch):
        """
        Replacer used by `re.sub` to replace ANSI
        bright background markers with Xterm256 replacement

        Args:
            ansimatch (re.matchobject): The match.

        Returns:
            processed (str): The processed match string.

        """
        return self.ansi_xterm256_bright_bg_map_dict.get(ansimatch.group(), "")

    def sub_xterm256(self, rgbmatch, use_xterm256=False, color_type="fg"):
        """
        This is a replacer method called by `re.sub` with the matched
        tag. It must return the correct ansi sequence.

        It checks `self.do_xterm256` to determine if conversion
        to standard ANSI should be done or not.

        Args:
            rgbmatch (re.matchobject): The match.
            use_xterm256 (bool, optional): Don't convert 256-colors to 16.
            color_type (str): One of 'fg', 'bg', 'gfg', 'gbg'.

        Returns:
            processed (str): The processed match string.

        """
        if not rgbmatch:
            return ""

        # get tag, stripping the initial marker
        # rgbtag = rgbmatch.group()[1:]

        background = color_type in ("bg", "gbg")
        grayscale = color_type in ("gfg", "gbg")

        if not grayscale:
            # 6x6x6 color-cube (xterm indexes 16-231)
            try:
                red, green, blue = [int(val) for val in rgbmatch.groups() if val is not None]
            except (IndexError, ValueError) as e:
                logging.exception(e)
                return rgbmatch.group(0)
        else:
            # grayscale values (xterm indexes 0, 232-255, 15) for full spectrum
            try:
                letter = [val for val in rgbmatch.groups() if val is not None][0]
            except IndexError as i:
                logging.exception(i)
                return rgbmatch.group(0)

            if letter == "a":
                colval = 16  # pure black @ index 16 (first color cube entry)
            elif letter == "z":
                colval = 231  # pure white @ index 231 (last color cube entry)
            else:
                # letter in range [b..y] (exactly 24 values!)
                colval = 134 + ord(letter)

            # ansi fallback logic expects r,g,b values in [0..5] range
            gray = (ord(letter) - 97) / 5.0
            red, green, blue = gray, gray, gray

        if use_xterm256:

            if not grayscale:
                colval = 16 + (red * 36) + (green * 6) + blue

            return "\033[%s8;5;%sm" % (3 + int(background), colval)
            # replaced since some clients (like Potato) does not accept codes with leading zeroes, see issue #1024.
            # return "\033[%s8;5;%s%s%sm" % (3 + int(background), colval // 100, (colval % 100) // 10, colval%10)

        else:
            # xterm256 not supported, convert the rgb value to ansi instead
            if red == green == blue and red < 3:
                if background:
                    return ANSI_BACK_BLACK
                elif red >= 1:
                    return ANSI_HILITE + ANSI_BLACK
                else:
                    return ANSI_NORMAL + ANSI_BLACK
            elif red == green == blue:
                if background:
                    return ANSI_BACK_WHITE
                elif red >= 4:
                    return ANSI_HILITE + ANSI_WHITE
                else:
                    return ANSI_NORMAL + ANSI_WHITE
            elif red > green and red > blue:
                if background:
                    return ANSI_BACK_RED
                elif red >= 3:
                    return ANSI_HILITE + ANSI_RED
                else:
                    return ANSI_NORMAL + ANSI_RED
            elif red == green and red > blue:
                if background:
                    return ANSI_BACK_YELLOW
                elif red >= 3:
                    return ANSI_HILITE + ANSI_YELLOW
                else:
                    return ANSI_NORMAL + ANSI_YELLOW
            elif red == blue and red > green:
                if background:
                    return ANSI_BACK_MAGENTA
                elif red >= 3:
                    return ANSI_HILITE + ANSI_MAGENTA
                else:
                    return ANSI_NORMAL + ANSI_MAGENTA
            elif green > blue:
                if background:
                    return ANSI_BACK_GREEN
                elif green >= 3:
                    return ANSI_HILITE + ANSI_GREEN
                else:
                    return ANSI_NORMAL + ANSI_GREEN
            elif green == blue:
                if background:
                    return ANSI_BACK_CYAN
                elif green >= 3:
                    return ANSI_HILITE + ANSI_CYAN
                else:
                    return ANSI_NORMAL + ANSI_CYAN
            else:  # mostly blue
                if background:
                    return ANSI_BACK_BLUE
                elif blue >= 3:
                    return ANSI_HILITE + ANSI_BLUE
                else:
                    return ANSI_NORMAL + ANSI_BLUE

    def strip_raw_codes(self, string):
        """
        Strips raw ANSI codes from a string.

        Args:
            string (str): The string to strip.

        Returns:
            string (str): The processed string.

        """
        return self.ansi_regex.sub("", string)

    def strip_mxp(self, string):
        """
        Strips all MXP codes from a string.

        Args:
            string (str): The string to strip.

        Returns:
            string (str): The processed string.

        """
        return self.mxp_sub.sub(r"\2", string)

    def parse_ansi(self, string, strip_ansi=False, xterm256=False, mxp=False):
        """
        Parses a string, subbing color codes according to the stored
        mapping.

        Args:
            string (str): The string to parse.
            strip_ansi (boolean, optional): Strip all found ansi markup.
            xterm256 (boolean, optional): If actually using xterm256 or if
                these values should be converted to 16-color ANSI.
            mxp (boolean, optional): Parse MXP commands in string.

        Returns:
            string (str): The parsed string.

        """
        if hasattr(string, "_raw_string"):
            if strip_ansi:
                return string.clean()
            else:
                return string.raw()

        if not string:
            return ""

        # check cached parsings
        global _PARSE_CACHE
        cachekey = "%s-%s-%s-%s" % (string, strip_ansi, xterm256, mxp)
        if cachekey in _PARSE_CACHE:
            return _PARSE_CACHE[cachekey]

        # pre-convert bright colors to xterm256 color tags
        string = self.brightbg_sub.sub(self.sub_brightbg, string)

        def do_xterm256_fg(part):
            return self.sub_xterm256(part, xterm256, "fg")

        def do_xterm256_bg(part):
            return self.sub_xterm256(part, xterm256, "bg")

        def do_xterm256_gfg(part):
            return self.sub_xterm256(part, xterm256, "gfg")

        def do_xterm256_gbg(part):
            return self.sub_xterm256(part, xterm256, "gbg")

        in_string = to_str(string)

        # do string replacement
        parsed_string = []
        parts = self.ansi_escapes.split(in_string) + [" "]
        for part, sep in zip(parts[::2], parts[1::2]):
            pstring = self.xterm256_fg_sub.sub(do_xterm256_fg, part)
            pstring = self.xterm256_bg_sub.sub(do_xterm256_bg, pstring)
            pstring = self.xterm256_gfg_sub.sub(do_xterm256_gfg, pstring)
            pstring = self.xterm256_gbg_sub.sub(do_xterm256_gbg, pstring)
            pstring = self.ansi_sub.sub(self.sub_ansi, pstring)
            parsed_string.append("%s%s" % (pstring, sep[0].strip()))
        parsed_string = "".join(parsed_string)

        if not mxp:
            parsed_string = self.strip_mxp(parsed_string)

        if strip_ansi:
            # remove all ansi codes (including those manually
            # inserted in string)
            return self.strip_raw_codes(parsed_string)

        # cache and crop old cache
        _PARSE_CACHE[cachekey] = parsed_string
        if len(_PARSE_CACHE) > _PARSE_CACHE_SIZE:
            _PARSE_CACHE.popitem(last=False)

        return parsed_string


ANSI_PARSER = ANSIParser()


#
# Access function
#


def parse_ansi(string, strip_ansi=False, parser=ANSI_PARSER, xterm256=False, mxp=False):
    """
    Parses a string, subbing color codes as needed.

    Args:
        string (str): The string to parse.
        strip_ansi (bool, optional): Strip all ANSI sequences.
        parser (ansi.AnsiParser, optional): A parser instance to use.
        xterm256 (bool, optional): Support xterm256 or not.
        mxp (bool, optional): Support MXP markup or not.

    Returns:
        string (str): The parsed string.

    """
    return parser.parse_ansi(string, strip_ansi=strip_ansi, xterm256=xterm256, mxp=mxp)


def strip_ansi(string, parser=ANSI_PARSER):
    """
    Strip all ansi from the string. This handles the Evennia-specific
    markup.

    Args:
        string (str): The string to strip.
        parser (ansi.AnsiParser, optional): The parser to use.

    Returns:
        string (str): The stripped string.

    """
    return parser.parse_ansi(string, strip_ansi=True)


def strip_raw_ansi(string, parser=ANSI_PARSER):
    """
    Remove raw ansi codes from string. This assumes pure
    ANSI-bytecodes in the string.

    Args:
        string (str): The string to parse.
        parser (bool, optional): The parser to use.

    Returns:
        string (str): the stripped string.

    """
    return parser.strip_raw_codes(string)


def raw(string):
    """
    Escapes a string into a form which won't be colorized by the ansi
    parser.

    Returns:
        string (str): The raw, escaped string.

    """
    return string.replace("{", "{{").replace("|", "||")


def EvenniaToRich(s: str) -> Text:
    ev = parse_ansi(s, xterm256=True, mxp=True)
    return Text("\n").join(AnsiDecoder().decode(ev))
