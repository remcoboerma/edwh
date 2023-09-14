"""
This file contains re-usable helpers.
"""
import sys
import typing

import diceware
from invoke import Argument, Context

from .extendable_fab import ExtendableFab

# from .cli import program # <- WILL BREAK TASK DETECTION!


def confirm(prompt: str, default: bool = False) -> bool:
    """
    Prompt a user to confirm a (dangerous) action.
    By default, entering nothing (only enter) will result in False, unless 'default' is set to True.
    """
    allowed = {"y", "1"}
    if default:
        allowed.add(" ")

    answer = input(prompt).lower().strip()
    answer += " "

    return answer[0] in allowed


def executes_correctly(c: Context, argument: str) -> bool:
    """returns True if the execution was without error level"""
    return c.run(argument, warn=True, hide=True).ok


def execution_fails(c: Context, argument: str) -> bool:
    """Returns true if the execution fails based on error level"""
    return not executes_correctly(c, argument)


def generate_password(silent=True):
    """Generate a diceware password using --dice 6."""
    password = diceware.get_passphrase()
    if not silent:
        print("Password:", password)
    return password


T = typing.TypeVar("T", str, bool)


def _add_dash(flag: str) -> str:
    if flag.startswith("-"):
        # don't change
        return flag
    if len(flag) == 1:
        # one letter, -x
        return f"-{flag}"
    else:
        # multiple letters --flag
        return f"--{flag}"


def arg_was_passed(flag: str | tuple[str, ...]) -> typing.Optional[int]:
    """
    Returns the index of the flag in sys.argv if passed, else None
    """
    flag = flag if isinstance(flag, tuple) else (flag,)
    flag = tuple(_add_dash(f) for f in flag)
    # flag and sys.argv should now both be in the same format: -x and --flag
    return next((i for i, item in enumerate(sys.argv) if item in flag), None)


def add_global_flag(
    flag: str | tuple[str, ...], flag_type: type[T], callback: typing.Callable[[T], typing.Any], doc: str = ""
):
    """
    Tasks can have their own flags, but if you want to add a 'core' flag to
    """
    if isinstance(flag, str):
        flag = (flag.strip("-"),)
    else:
        flag = tuple(f.strip("-") for f in flag)

    # core_args are saved in a class variable, so they can be prepared before an actual invoke/fab program instance.
    ExtendableFab.add_core_arg(
        Argument(
            names=flag,
            kind=flag_type,
            help=(doc or callback.__doc__ or "").strip(),
        )
    )

    # normally you would access an Argument via program.args but that depends on program.core,
    # which does not exist yet at this point!
    # so we do it manually below, and the Argument added above is only for documentation.

    if not (idx := arg_was_passed(flag)):
        # arg not in cli, skip!
        return

    args = sys.argv
    args.pop(idx)

    value: T
    if flag_type == str:
        value = args.pop(idx)  # idx + 1 but args was already updated
    else:
        value = True

    return callback(value)
