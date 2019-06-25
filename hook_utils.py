"""Shared functions and settings for Python git hooks for M3D"""

import sys
import re
from subprocess import check_output, CalledProcessError
from typing import List, Tuple

GIT_DEFAULT_COMMENT_CHAR = "#"
GIT_VERBOSE_HEADER = " ------------------------ >8 ------------------------"

FEATURE_BRANCH_RE = r"^[fF]eature/[a-zA-Z]{1,3}(\d+)_.*"
PROTO_BRANCH_RE = r"^[pP]roto/[a-zA-Z]{1,3}(\d+)_.*"
LEGACY_FEATURE_BRANCH_RE = r"^(\d+)_.*"
ISSUE_NUMBER_RE = r"^\s?#(\d+)\s.*"
COMMIT_MSG_RE = r"^(\s?#\d+\s.*|[mM]erge\s.*)"


# Get git comment char
def get_git_comment_char() -> Tuple[str, str]:
    msg = ""
    try:
        comment_char = (
            check_output(["git", "config", "--get", "core.commentChar"])
            .strip()
            .decode(encoding="UTF-8")
        )
    except CalledProcessError as e:
        if e.returncode == 1:
            comment_char = GIT_DEFAULT_COMMENT_CHAR
            msg = (
                "No comment char configured, it is advised to configure "
                "core.commentChar to use # for issue numbers\n"
            )
        else:
            raise
    return comment_char, msg


def get_issue_num_by_branch() -> Tuple[str, str]:
    msg = ""
    branch_name = (
        check_output(["git", "symbolic-ref", "--short", "HEAD"])
        .strip()
        .decode(encoding="UTF-8")
    )
    feature_match = re.match(FEATURE_BRANCH_RE, branch_name)
    if feature_match:
        return feature_match.group(1), msg
    legacy_feature_match = re.match(LEGACY_FEATURE_BRANCH_RE, branch_name)
    if legacy_feature_match:
        msg = (
            "You're using a legacy branch naming convention, consider adopting: "
            "feature/[2 char initial][Issue number], e.g. feature/DD1000_example\n"
        )
        return legacy_feature_match.group(1), msg
    proto_match = re.match(PROTO_BRANCH_RE, branch_name)
    if proto_match:
        return proto_match.group(1), msg
    msg = "Could not determine issue number by branch name\n"
    return None, msg


def open_console_input():
    if sys.platform == "win32":
        sys.stdin = open("CON:")
    else:
        sys.stdin = open("/dev/tty")


def ask_user_choice(message: str, options: List[str]):
    options_casefold = map(str.casefold, options)
    option_chars = [opt[0].casefold() for opt in options]
    user_input = input(
        f"{message}"
        f"{', '.join(options[:-1])} or {options[-1]}? "
        f"[{'/'.join(option_chars)}]"
    )
    user_input = user_input.casefold()
    while (user_input not in options_casefold) and (user_input not in option_chars):
        user_input = input(
            f"Invalid choice {user_input}. "
            f"{','.join(options[:-1])} or {options[-1]}? "
            f"[{'/'.join(option_chars)}]"
        )
    for opt, opt_char in zip(options, option_chars):
        if user_input == opt.casefold() or user_input == opt_char:
            return opt
