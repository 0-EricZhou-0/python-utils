from __future__ import annotations

import io, logging
import sys
import enum

import common_util.env_variable as env
import typing

# respect NO_COLOR and terminal property
no_color = env.no_color()

def color_settings(force_color: bool = False):
    global no_color
    no_color = force_color

def isatty(stream: typing.TextIO) -> bool:
    try:
        return stream.isatty()
    except AttributeError:
        return False

class ANSICompose(enum.Enum):
    @staticmethod
    def compose(*args: ANSICompose | int | str) -> str:
        return f"\033[{';'.join(map(str, args))}m"

    @staticmethod
    def compose256color(value: int, foreground: bool = True) -> str:
        """
        >   0-  7:  standard colors (as in ESC [ 30-37 m)
        >   8- 15:  high intensity colors (as in ESC [ 90-97 m)
        >  16-231:  6 * 6 * 6 cube (216 colors): 16 + 36 * r + 6 * g + b (0 ≤ r, g, b ≤ 5)
        > 232-255:  grayscale from dark to light in 24 steps
        """
        if foreground:
            return f"{ANSICompose.FORE_COLOR};5;{value}"
        return f"{ANSICompose.BACK_COLOR};5;{value}"

    @staticmethod
    def composeRGB(r: int, g: int, b: int, foreground: bool = True) -> str:
        """
        2;{r};{g};{b} for RGB colors
        r, g, b should be in range 0-255
        """
        if foreground:
            return f"{ANSICompose.FORE_COLOR};2;{r};{g};{b}"
        return f"{ANSICompose.BACK_COLOR};2;{r};{g};{b}"

    def __str__(self) -> str:
        return str(self.value)

    # endc
    ENDC         = 0
    # styles
    BOLD         = 1
    FAINT        = 2
    ITALIC       = 3
    UNDERLINE    = 4
    BLINK        = 5
    NEGATIVE     = 7
    CROSSED      = 9
    # foreground colors
    FORE_BLACK   = 30
    FORE_RED     = 31
    FORE_GREEN   = 32
    FORE_YELLOW  = 33
    FORE_BLUE    = 34
    FORE_MAGENTA = 35
    FORE_CYAN    = 36
    FORE_WHITE   = 37
    FORE_COLOR   = 38
    FORE_TRANS   = 39
    # background colors
    BACK_BLACK   = 40
    BACK_RED     = 41
    BACK_GREEN   = 42
    BACK_YELLOW  = 43
    BACK_BLUE    = 44
    BACK_MAGENTA = 45
    BACK_CYAN    = 46
    BACK_WHITE   = 47
    BACK_COLOR   = 48
    BACK_TRANS   = 49

class ANSIColors:
    BLACK   = ANSICompose.compose(ANSICompose.FORE_BLACK)
    RED     = ANSICompose.compose(ANSICompose.FORE_RED)
    GREEN   = ANSICompose.compose(ANSICompose.FORE_GREEN)
    YELLOW  = ANSICompose.compose(ANSICompose.FORE_YELLOW)
    BLUE    = ANSICompose.compose(ANSICompose.FORE_BLUE)
    MAGENTA = ANSICompose.compose(ANSICompose.FORE_MAGENTA)
    CYAN    = ANSICompose.compose(ANSICompose.FORE_CYAN)
    WHITE   = ANSICompose.compose(ANSICompose.FORE_WHITE)

    BOLD_RED = ANSICompose.compose(ANSICompose.FORE_RED, ANSICompose.BOLD)

    ENDC = ANSICompose.compose(ANSICompose.ENDC)


class MessageLevel(enum.Enum):
    EMERG   = 0
    ALERT   = 1
    CRIT    = 2  # critical conditions
    ERR     = 3  # error conditions
    WARNING = 4  # warning conditions
    NOTICE  = 5  # normal but significant condition
    INFO    = 6  # informational
    DEBUG   = 7  # debug-level messages


class ColoredPrintSetting:
    MSG_COLOR_DICT: dict[int, str] = {
        logging.CRITICAL: ANSICompose.compose(ANSICompose.FORE_RED, ANSICompose.BOLD),
        logging.ERROR:    ANSICompose.compose(ANSICompose.FORE_RED),
        logging.WARNING:  ANSICompose.compose(ANSICompose.FORE_YELLOW),
        logging.INFO:     ANSICompose.compose(ANSICompose.FORE_BLUE),
        logging.DEBUG:    ANSICompose.compose(ANSICompose.FORE_CYAN),
    }


def pprintf(ansi_color_str: typing.Union[str, ANSIColors], *args, **kwargs) -> None:
    if no_color:
        print(*args, **kwargs)
    else:
        output_str = io.StringIO()
        with io.StringIO() as output_str:
            print(*args, file=output_str, end="")
            print(f"{ansi_color_str}{output_str.getvalue()}{ANSIColors.ENDC}", **kwargs)


def cprintf(*args, **kwargs):
    """Argument list same as print"""
    return pprintf(
        ColoredPrintSetting.MSG_COLOR_DICT[logging.CRITICAL], *args, **kwargs
    )


def eprintf(*args, **kwargs):
    """Argument list same as print"""
    return pprintf(
        ColoredPrintSetting.MSG_COLOR_DICT[logging.ERROR], *args, **kwargs
    )


def wprintf(*args, **kwargs):
    """Argument list same as print"""
    return pprintf(
        ColoredPrintSetting.MSG_COLOR_DICT[logging.WARNING], *args, **kwargs
    )


def iprintf(*args, **kwargs):
    """Argument list same as print"""
    return pprintf(
        ColoredPrintSetting.MSG_COLOR_DICT[logging.INFO], *args, **kwargs
    )


def dprintf(*args, **kwargs):
    """Argument list same as print"""
    return pprintf(
        ColoredPrintSetting.MSG_COLOR_DICT[logging.DEBUG], *args, **kwargs
    )


def __check_level(level: typing.Union[str, int]) -> int:
    # copying logging._checkLevel
    if isinstance(level, int):
        rv = level
    elif str(level) == level:
        if level not in logging._nameToLevel:
            raise ValueError("Unknown level: %r" % level)
        rv = logging._nameToLevel[level]
    else:
        raise TypeError("Level not an integer or a valid string: %r" % (level,))
    return rv


def lprintf(level: typing.Union[str, int], *args, **kwargs):
    """First arg is logging level Argument list same as print"""
    return pprintf(
        ColoredPrintSetting.MSG_COLOR_DICT[__check_level(level)], *args, **kwargs
    )
