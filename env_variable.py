"""
Provides functions to check and manipulate environment variables.
"""

import os, functools

IS_DEBUG_ENVIRON = "DEBUG"
NO_COLOR_ENVIRON = "NO_COLOR"


def check_env(env: str) -> str | None:
    """
    Check if the environment variable exists and return its value.
    @param env The name of the environment variable to check.
    @return The value of the environment variable, or None if it does not exist.
    """
    return os.environ.get(env, None)


def check_env_exists(env: str) -> bool:
    """
    Check if the environment variable exists.
    @param env The name of the environment variable to check.
    """
    return env in os.environ


def check_env_exists_and_not_empty(env: str) -> bool:
    """
    Check if the environment variable exists and is not an empty string.
    @param env The name of the environment variable to check.
    """
    val = os.environ.get(env, None)
    return val is not None and len(val) != 0


def check_env_true(env: str) -> bool:
    """
    A environment variable is considered true if the variable exists and it is
    1) an integer with non-zero value, or
    2) a non-empty string
    @param env The name of the environment variable to check.
    """
    val = os.environ.get(env, None)
    if val is None:
        return False
    is_digit = val.isdigit()
    return (is_digit and int(val) != 0) or (not is_digit and len(val) != 0)


def set_env(env: str, val: str | int) -> None | str:
    """
    Set an environment variable to a value. If the environment variable already exists, return its
    previous value.
    @param env The name of the environment variable to set.
    @param val The value to set the environment variable to.
    @return The previous value of the environment variable, or None if it did not exist.
    """
    ret = os.environ.get(env, None)
    if isinstance(val, int):
        val = str(val)
    os.environ[env] = val
    return ret


@functools.cache
def is_debug() -> bool:
    """
    Check if the DEBUG environment variable is set.
    @note: This function caches the result to ensure consistent result.
    """
    return check_env_exists(IS_DEBUG_ENVIRON)


@functools.cache
def no_color() -> bool:
    """
    Check if the NO_COLOR environment variable is set.
    @note: This function caches the result to ensure consistent result.
    """
    return check_env_exists_and_not_empty(NO_COLOR_ENVIRON)
