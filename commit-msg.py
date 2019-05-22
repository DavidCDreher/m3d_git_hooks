#!/usr/bin/env python3

# Borrowed from: http://addamhardy.com/blog/2013/06/05/good-commit-messages-and-enforcing-them-with-git-hooks/
# With modifications by: Jon Roelofs <jonathan@codesourcery.com>

import sys
import os
import re
from subprocess import call

import hook_utils

if os.environ.get("EDITOR", "none") != "none":
    editor = os.environ["EDITOR"]
else:
    editor = "vim"


def check_format_first_line(line, git_comment_char):
    error_msg = ""
    if not re.match(hook_utils.COMMIT_MSG_RE, line):
        msg = (
                git_comment_char
                + " Error: Subject line should start with a #(ISSUE) or with 'Merge'\n"
        )
        error_msg = error_msg + msg
        issue_match = re.match(hook_utils.ISSUE_NUMBER_RE, line)
        issue_branch_number, number_msg = hook_utils.get_issue_num_by_branch()
        if number_msg:
            error_msg += git_comment_char + number_msg
        if issue_match and issue_branch_number:
            if issue_match.group(1) != issue_branch_number:
                msg = (
                        git_comment_char
                        + " Error: Mismatch between branch issue number and issue number in commit message\n"
                )
                error_msg = error_msg + msg
    if len(line) > 50:
        msg = git_comment_char + " Error: Limit the subject line to 50 characters"
        error_msg = (
            error_msg
            + msg
            + (" " * (50 - 1 - len(msg)))
            + "^"
            + ("~" * (len(line) - 50 - 1))
            + "\n"
        )
    first_word_re = "[^a-zA-Z]*([a-zA-Z]+).*"
    first_word_match = re.match(first_word_re, line)
    if first_word_match:
        first_word = first_word_match.group(1)
        if first_word[0].islower():
            msg = git_comment_char + " Error: Capitalize the subject line\n"
            error_msg = error_msg + msg
    else:
        msg = git_comment_char + " Error: Subject line should include a summary\n"
        error_msg = error_msg + msg
    if line and line[-1] == ".":
        msg = git_comment_char + " Error: Do not end the subject line with a period\n"
        error_msg = error_msg + msg
    return error_msg


def check_format_rules(line_num, line, git_comment_char):
    if line_num == 0:
        return check_format_first_line(line, git_comment_char)
    if line_num == 1:
        if line:
            return git_comment_char + " Error: Second line ^ should be empty.\n"
    if not line.startswith(git_comment_char):
        if len(line) > 80:
            err_msg = git_comment_char + " Error: No line should exceed 80 characters:"
            err_msg = (
                err_msg
                + (" " * (80 - 1 - len(err_msg)))
                + "^"
                + ("~" * (len(line) - 80 - 1))
                + "\n"
            )
            return err_msg
    return False


if __name__ == "__main__":
    message_file = sys.argv[1]
    try:
        comment_char, comment_msg = hook_utils.get_git_comment_char()
        while True:
            new_commit_msg = list()
            errors = False
            with open(message_file) as commit_fd:
                line_number = -1
                for curr_line in commit_fd:
                    stripped_line = curr_line.strip()
                    # Stop reading in case of verbose mode when encountering header
                    if stripped_line.startswith(comment_char + hook_utils.GIT_VERBOSE_HEADER):
                        break
                    # Read only non-comment lines
                    if not stripped_line.startswith(comment_char):
                        line_number += 1
                        new_commit_msg.append(curr_line)
                        e = check_format_rules(line_number, stripped_line, comment_char)
                        if (line_number == 0) and comment_msg:
                            e += comment_char + comment_msg
                        if e:
                            new_commit_msg.append(e)
                            errors = True
            if errors:
                with open(message_file, "w") as commit_fd:
                    for curr_line in new_commit_msg:
                        commit_fd.write(curr_line)
                    commit_fd.write("\n")
                user_msg = "Errors in commit message format. "
                user_options = ["Abort", "edit", "ignore"]
                user_choice = hook_utils.ask_user_choice(user_msg, user_options)
                if user_choice == "Abort":
                    sys.exit(1)
                elif user_choice == "ignore":
                    sys.exit(0)
                else:
                    call(["env", editor, message_file])
                    continue
            else:
                sys.exit(0)
    except KeyboardInterrupt:
        print("Abort by keyboard interrupt")
        sys.exit(1)
