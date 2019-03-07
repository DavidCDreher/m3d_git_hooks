#!/usr/bin/env python3

# Borrowed from: http://addamhardy.com/blog/2013/06/05/good-commit-messages-and-enforcing-them-with-git-hooks/
# With modifications by: Jon Roelofs <jonathan@codesourcery.com>

import sys
import os
import re
from subprocess import call, check_output, CalledProcessError

commit_msg_re = r"^(#\d+\s.*|[mM]erge\s.*)"
issue_number_re = r"^#(\d+)\s.*"
feature_branch_re = r"^[fF]eature/[a-zA-Z]{1,3}(\d+)_.*"
legacy_feature_branch_re = r"^(\d+)_.*"

git_verbose_header = " ------------------------ >8 ------------------------"

if os.environ.get("EDITOR", "none") != "none":
    editor = os.environ["EDITOR"]
else:
    editor = "vim"

# Get git comment char
try:
    comment_char = (
        check_output(["git", "config", "--get", "core.commentChar"])
        .strip()
        .decode(encoding="UTF-8")
    )
except CalledProcessError as e:
    if e.returncode == 1:
        comment_char = "#"
        print(
            "No comment char configured, it is advised to configure core.commentChar to use # for issue numbers"
        )
    else:
        raise


def get_issue_num_by_branch():
    branch_name = (
        check_output(["git", "symbolic-ref", "--short", "HEAD"])
        .strip()
        .decode(encoding="UTF-8")
    )
    feature_match = re.match(feature_branch_re, branch_name)
    if feature_match:
        return feature_match.group(1)
    legacy_feature_match = re.match(legacy_feature_branch_re, branch_name)
    if legacy_feature_match:
        print(
            "You're using a legacy branch naming convention, consider adopting: "
            + feature_branch_re
        )
        return legacy_feature_match.group(1)
    return None


def check_format_first_line(line):
    error_msg = ""
    if not re.match(commit_msg_re, line):
        msg = (
            comment_char
            + " Error: Subject line should start with a #(ISSUE) or with 'Merge'\n"
        )
        error_msg = error_msg + msg
        issue_match = re.match(issue_number_re, line)
        issue_branch_number = get_issue_num_by_branch()
        if issue_match and issue_branch_number:
            if issue_match.group(1) != issue_branch_number:
                msg = (
                    comment_char
                    + " Error: Mismatch between branch issue number and issue number in commit message\n"
                )
                error_msg = error_msg + msg
    if len(line) > 50:
        msg = comment_char + " Error: Limit the subject line to 50 characters"
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
            msg = comment_char + " Error: Capitalize the subject line\n"
            error_msg = error_msg + msg
    else:
        msg = comment_char + " Error: Subject line should include a summary\n"
        error_msg = error_msg + msg
    if line and line[-1] == ".":
        msg = comment_char + " Error: Do not end the subject line with a period\n"
        error_msg = error_msg + msg
    return error_msg


def check_format_rules(line_num, line):
    if line_num == 0:
        return check_format_first_line(line)
    if line_num == 1:
        if line:
            return comment_char + " Error: Second line ^ should be empty.\n"
    if not line.startswith(comment_char):
        if len(line) > 80:
            err_msg = comment_char + " Error: No line should exceed 80 characters:"
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

        while True:
            new_msg = list()
            errors = False
            with open(message_file) as commit_fd:
                line_number = -1
                for curr_line in commit_fd:
                    stripped_line = curr_line.strip()
                    # Stop reading in case of verbose mode when encountering header
                    if stripped_line.startswith(comment_char + git_verbose_header):
                        break
                    # Read only non-comment lines
                    if not stripped_line.startswith(comment_char):
                        line_number += 1
                        new_msg.append(curr_line)
                        e = check_format_rules(line_number, stripped_line)
                        if e:
                            new_msg.append(e)
                            errors = True
            if errors:
                with open(message_file, "w") as commit_fd:
                    for curr_line in new_msg:
                        commit_fd.write(curr_line)
                    commit_fd.write("\n")
                re_edit = input(
                    "Errors in commit message format. Abort, Edit, or Ignore?. [a/e/i] "
                )
                while re_edit not in ("a", "abort", "e", "edit", "i", "ignore"):
                    re_edit = input(
                        "Invalid choice '%s'.  Abort, Edit, or Ignore?. [a/e/i] "
                        % (re_edit,)
                    )
                if re_edit.lower() in ("a", "abort"):
                    sys.exit(1)
                elif re_edit.lower() in ("i", "ignore"):
                    sys.exit(0)
                else:
                    call(["env", editor, message_file])
                    continue
            else:
                sys.exit(0)
    except KeyboardInterrupt:
        print("Abort by keyboard interrupt")
        sys.exit(1)
