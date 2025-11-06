"""
Include useful Python utilities that are not part of the standard library.
"""

import os, sys
import hashlib
import typing
import time
import datetime
import fcntl
import re


# NOTE [Python typing on SupportsRead and SupportsWrite]:
# The typing module does not provide SupportsRead and SupportsWrite instances for runtime type
# checking, a custom implementation is provided below. The str version for SupportsRead and
# SupportsWrite is provided below.
@typing.runtime_checkable
class SupportsReadStr(typing.Protocol):
    def read(self, size: typing.Optional[int] = -1, /) -> str: ...


@typing.runtime_checkable
class SupportsWriteStr(typing.Protocol):
    def write(self, data: str, /) -> None: ...


def get_script_path(file: str) -> str:
    """
    Get the absolute path of the script file, resolving symlinks.
    :param file: The script file name or path.
    :return: The absolute path of the script file.
    """
    return os.path.realpath(file)


def get_script_dir(file: str) -> str:
    """
    Get the directory of the script file.
    :param file: The script file name or path.
    :return: The directory of the script file.
    """
    return os.path.dirname(get_script_path(file))


def printerr(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def safeval(val, default):
    if val:
        return val
    return default


def hash_file(algo, path, bufsize=131072):
    assert algo in hashlib.algorithms_available, f"Hash algorithm {algo} is not supported"
    assert os.path.isfile(path), f"File \"{path}\" does not exist (Working dir \"{os.getcwd()}\")"
    hs = hashlib.new(algo)
    buf = bytearray(bufsize)
    mv = memoryview(buf)
    with open(path, "rb", buffering=0) as fin:
        while nbytes := fin.readinto(mv):
            hs.update(mv[:nbytes])
    return hs.hexdigest()


dependency_check_funcs = {
    "f": lambda s: os.path.isfile(s),
    "d": lambda s: os.path.isdir(s),
    "e": lambda s: os.access(s, os.F_OK),
    "r": lambda s: os.access(s, os.R_OK),
    "w": lambda s: os.access(s, os.W_OK),
    "x": lambda s: os.access(s, os.X_OK),
}


def check_dependency(test_type, dependency) -> typing.Optional[str]:
    func = dependency_check_funcs.get(test_type)
    assert func is not None, f"Invalid type string {test_type}"

    if func(dependency):
        return os.path.realpath(dependency)


def find_device_for_path(path: str, device_name_only: bool = True) -> typing.Optional[str]:
    path = os.path.realpath(path)
    if not os.path.exists(path):
        return None
    dev = os.stat(path).st_dev

    try:
        with open("/proc/mounts") as f:
            for line in f:
                line_split = line.split()
                target_dev, mount_point, *_ = line_split
                try:
                    if os.stat(mount_point).st_dev == dev:
                        if device_name_only:
                            return os.path.basename(target_dev)
                        return target_dev
                except Exception:
                    continue
    except FileNotFoundError:
        return None
    return None


def display_options(
    option_list: dict[str, str],
    default_option: str,
    print_long_descriptions: bool = False,
    message: str = "",
    *args: list[str],
) -> str:
    default_mark_str = "(default) "
    option_list_copy = option_list.copy()
    message = message.format(*args) if len(message) != 0 else ""
    is_short_format = all(len(option) == 1 for option in option_list.keys())
    assert default_option in option_list, "Default option must be in the option list."
    assert all(
        option.islower() for option in option_list.keys()
    ), "All options must be in lowercase letters."
    print_delimiter = "" if is_short_format else "/"
    max_opt_len = max(len(option) for option in option_list.keys())
    display_option_list = [
        (
            option
            if option != default_option
            else (option.upper() if is_short_format else f"[{option}]")
        )
        for option in option_list.keys()
    ]
    if print_long_descriptions:
        for option, description in option_list_copy.items():
            is_default_option = option == default_option
            default_str = ""
            if is_default_option:
                default_str = default_mark_str
                option = option.upper() if is_short_format else f"[{option}]"
            message += (
                f"\n{default_str:{len(default_mark_str)}s}{option:<{max_opt_len}s}: {description}"
            )
    display_options_str = print_delimiter.join(display_option_list)
    message += f"\n  Selection" if print_long_descriptions else ""
    message += f" ({display_options_str}) ? "
    repeat_message = f"Invalid selection ({display_options_str}) ? "
    while True:
        selection = input(message).strip().lower()
        if len(selection) == 0:
            return default_option
        if selection in option_list.keys():
            return selection
        message = repeat_message


def display_yn_option(message: str = "", *args: list[str]) -> bool:
    yn_options = {"y": "Confirm", "n": "Deny"}
    selection = display_options(
        yn_options, default_option="n", print_long_descriptions=False, message=message, *args
    )
    return selection == "y"


def acquireLockFile(lock_file: str):
    """
    Acquire an exclusive lock on a file.
    @param lock_file: The path to the lock file.
    @return: A file descriptor for the locked file.
    @raises OSError: If the lock cannot be acquired.
    """
    locked_file_descriptor = open(lock_file, "w+")
    try:
        # non-blocking and exclusive lock
        fcntl.lockf(locked_file_descriptor, fcntl.LOCK_NB | fcntl.LOCK_EX)
    except OSError as e:
        printerr(
            f"Could not get lock {lock_file} - {e.errno}: {e.strerror}.\n"
            f"Unable to acquire the lock, is another process using it? "
        )
        raise e
    return locked_file_descriptor


def releaseLockFile(locked_file_descriptor):
    """
    Release the lock on a file and close the file descriptor.
    @param locked_file_descriptor: The file descriptor for the locked file.
    """
    locked_file_descriptor.close()


# handle time formats like "2025-10-04T11:49:20.880Z"
def parse_time(time_str: str, format: re.Pattern) -> typing.Optional[time.struct_time]:
    """
    Parse a time string into a struct_time object.
    @param time_str The time string to parse.
    @param format The format string to use for parsing.
    @return A struct_time object if parsing is successful, None otherwise.
    """
    match = format.match(time_str)
    total_struct_len = 8
    if match and len(match.groups()) < total_struct_len:
        return time.struct_time((
            *match.groups(),
            *(0 for _ in range(total_struct_len - len(match.groups()))),
            -1 # daylight savings time flag always false
        ))
    return None

def parse_iso_time_format(time_str: str) -> typing.Optional[datetime.datetime]:
    try:
        return datetime.datetime.fromisoformat(time_str[:-1])
    except ValueError:
        return None


# this is faster than get_first_word_re in practice for line with date info at the beginning of line
def get_first_word(line: str) -> str:
    """
    Get the first word from a line.
    The first word is defined as the first sequence of non-whitespace characters.
    @param line The input line.
    @return The first word in the line.
    """
    # raise NotImplementedError()
    leading_space_end = -1
    for i, c in enumerate(line):
        if c.isspace():
            if leading_space_end < -1:
                # the space is a leading space, go on
                continue
            # the space first seen, perform substring
            return line[leading_space_end + 1 : i]
        elif leading_space_end < -1:
            # encountered first non-space character
            leading_space_end = i - 1
    return line[leading_space_end + 1 :]


first_word_re = re.compile(r"^\s*(\S+)")


def get_first_word_re(line: str) -> str:
    """
    Get the first word from a line using a regular expression.
    The first word is defined as the first sequence of non-whitespace characters.
    @param line The input line.
    @return The first word in the line.
    """
    match = first_word_re.match(line)
    return match.group(1) if match else line


def get_line_without_first_word(line: str) -> str:
    """
    Get the line without the first word.
    The first word is defined as the first sequence of non-whitespace characters.
    @param line The input line.
    @return The line without the first word.
    """
    leading_space_end = -2
    leading_word_end = -1
    for i, c in enumerate(line):
        if c.isspace():
            if leading_space_end >= -1:
                leading_word_end = i - 1
        else:
            if leading_space_end < -1:
                leading_space_end = i - 1
            elif leading_word_end >= 0:
                return line[i:]
    return ""


# This is faster than get_line_without_first_word in practice for long lines
line_without_first_word_re = re.compile(r"^\s*\S+\s*(.*\r?\n)")


def get_line_without_first_word_re(line: str) -> str:
    """
    Get the line without the first word using a regular expression.
    The first word is defined as the first sequence of non-whitespace characters.
    @param line The input line.
    @return The line without the first word.
    """
    match = line_without_first_word_re.match(line)
    return match.group(1) if match else line
