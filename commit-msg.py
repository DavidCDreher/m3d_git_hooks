#!/usr/bin/env python3

# Borrowed from: http://addamhardy.com/blog/2013/06/05/good-commit-messages-and-enforcing-them-with-git-hooks/
# With modifications by: Jon Roelofs <jonathan@codesourcery.com>

import sys
import os
import re
from subprocess import call
from typing import List, Tuple
from _io import TextIOWrapper

import hook_utils

if os.environ.get("EDITOR", "none") != "none":
    editor = os.environ["EDITOR"]
else:
    editor = "vim"


def marker_at_line_pos(pos: int, end: int, offset: int) -> str:
    if pos <= offset:
        ValueError("Invalid starting offset")
    return f"{' ' * (pos - 1 - offset)}^{'~' * (end - pos - 1)}\n"


def check_format_first_line(line: str, git_comment_char: str) -> List[str]:
    messages = []
    if not re.match(hook_utils.COMMIT_MSG_RE, line):
        messages.append(
            f"{git_comment_char} Error: Subject line should start with a "
            f"#(ISSUE) or with 'Merge'\n"
        )
        issue_match = re.match(hook_utils.ISSUE_NUMBER_RE, line)
        issue_branch_number, _ = hook_utils.get_issue_num_by_branch()
        if issue_match and issue_branch_number:
            if issue_match.group(1) != issue_branch_number:
                messages.append(
                    f"{git_comment_char} Error: Mismatch between branch issue "
                    f"number and issue number in commit message\n"
                )
    if len(line) > 50:
        msg = f"{git_comment_char} Error: Limit the subject line to 50 characters"
        messages.append(msg + marker_at_line_pos(50, len(line), len(msg)))
    first_word_re = "[^a-zA-Z]*([a-zA-Z]+).*"
    first_word_match = re.match(first_word_re, line)
    if first_word_match:
        first_word = first_word_match.group(1)
        if first_word[0].islower():
            messages.append(f"{git_comment_char} Error: Capitalize the subject line\n")
    else:
        messages.append(
            f"{git_comment_char} Error: Subject line should include a summary\n"
        )
    if line and line[-1] == ".":
        messages.append(
            f"{git_comment_char} Error: Do not end the subject line with a period\n"
        )
    return messages


def parse_commit_message(commit_file_object: TextIOWrapper) -> Tuple[List[str], bool]:
    comment_char, _ = hook_utils.get_git_comment_char()
    reached_verbose_body = False
    mod_commit_msg = []
    line_number = -1
    contains_errors = False
    for line in commit_file_object:
        if hook_utils.GIT_VERBOSE_HEADER in line:
            reached_verbose_body = True
        if reached_verbose_body:
            mod_commit_msg.append(line)
            continue
        if not line.startswith(f"{comment_char} Error: "):
            line_number += 1
            mod_commit_msg.append(line)
            if line_number == 0:
                err_msgs = check_format_first_line(line, comment_char)
                if err_msgs:
                    mod_commit_msg.extend(err_msgs)
                    contains_errors = True
            elif not line.startswith(comment_char):
                if line_number == 1 and line.strip():
                    mod_commit_msg.append(
                        f"{comment_char} Error: Second line ^ should be empty.\n"
                    )
                    contains_errors = True
                elif len(line) > 80:
                    msg = f"{comment_char} Error: No line should exceed 80 characters:"
                    mod_commit_msg.append(msg + marker_at_line_pos(80, len(line), len(msg)))
                    contains_errors = True
    return mod_commit_msg, contains_errors


if __name__ == "__main__":
    message_file = sys.argv[1]
    try:
        while True:
            with open(message_file) as commit_fd:
                commit_msg, has_errors = parse_commit_message(commit_fd)
            if has_errors:
                with open(message_file, "w") as commit_fd:
                    commit_fd.writelines(commit_msg)
                user_msg = "Errors in commit message format. "
                user_options = ["Abort", "edit", "ignore"]
                user_choice = hook_utils.ask_user_choice(user_msg, user_options)
                if user_choice == "Abort":
                    sys.exit(1)
                elif user_choice == "ignore":
                    sys.exit(0)
                else:
                    call([editor, message_file])
                    continue
            else:
                sys.exit(0)
    except KeyboardInterrupt:
        print("Abort by keyboard interrupt")
        sys.exit(1)
