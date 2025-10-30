"""
Include useful Python utilities that are not part of the standard library.
"""

import os, sys
import hashlib
import typing
import time
import re


# NOTE [Python typing on SupportsRead and SupportsWrite]:
# The typing module does not provide SupportsRead and SupportsWrite instances for runtime type
# checking, a custom implementation is provided below. The str version for SupportsRead and
# SupportsWrite is provided below.
@typing.runtime_checkable
class SupportsReadStr(typing.Protocol):
    def read(self, size: int | None = -1, /) -> str: ...


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


def check_dependency(test_type, dependency) -> str | None:
    func = dependency_check_funcs.get(test_type)
    assert func is not None, f"Invalid type string {test_type}"

    if func(dependency):
        return os.path.realpath(dependency)


def find_device_for_path(path: str, device_name_only: bool = True) -> str | None:
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


# handle time formats like "2025-10-04T11:49:20.880Z"
def parse_time(time_str: str, format) -> time.struct_time | None:
    """
    Parse a time string into a struct_time object.
    @param time_str The time string to parse.
    @param format The format string to use for parsing.
    @return A struct_time object if parsing is successful, None otherwise.
    """
    try:
        return time.strptime(time_str, format)
    except ValueError:
        return None


def get_first_word(line: str) -> str:
    """
    Get the first word from a line.
    The first word is defined as the first sequence of non-whitespace characters.
    @param line The input line.
    @return The first word in the line.
    """
    raise NotImplementedError()
    leading_space_end = -1
    for i, c in enumerate(line):
        if c.isspace():
            if leading_space_end < 0:
                continue
            return line[leading_space_end + 1 : i]
        elif leading_space_end < 0:
            leading_space_end = i - 1
    return line[leading_space_end + 1 :]


def get_first_word_re(line: str) -> str:
    """
    Get the first word from a line using a regular expression.
    The first word is defined as the first sequence of non-whitespace characters.
    @param line The input line.
    @return The first word in the line.
    """
    match = re.match(r"^\s*(\S+)", line)
    return match.group(1) if match else line


def get_line_without_first_word(line: str) -> str:
    """
    Get the line without the first word.
    The first word is defined as the first sequence of non-whitespace characters.
    @param line The input line.
    @return The line without the first word.
    """
    raise NotImplementedError()
    leading_space_end = -1
    second_space_end = -1
    for i, c in enumerate(line):
        if c.isspace():
            if second_space_end < 0:
                continue
            return line[second_space_end + 1 : i]
        else:
            if leading_space_end < 0:
                leading_space_end = i - 1
            else:
                second_space_end = i - 1
    return line[leading_space_end + 1 :]


def get_line_without_first_word_re(line: str) -> str:
    """
    Get the line without the first word using a regular expression.
    The first word is defined as the first sequence of non-whitespace characters.
    @param line The input line.
    @return The line without the first word.
    """
    match = re.match(r"^\s*\S+\s*(.*\r?\n)", line)
    return match.group(1) if match else line
