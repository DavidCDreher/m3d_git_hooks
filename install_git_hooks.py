#!/usr/bin/env python3
"""Install utility for M3D git hooks"""

# stdlib
import sys
import shutil
import os
import stat
from subprocess import check_output, CalledProcessError

# external
import click


HOOK_FILES = [
    "prepare-commit-msg",
    "commit-msg",
    "pre-commit",
    "commit-msg.py",
    "hook_utils.py",
]
BACKUP_EXT = ".backup"


class InstallException(Exception):
    """Exception occurred while installing git hooks"""


def get_target_dir(target_dir: str) -> str:
    hook_dir = os.path.join(".git", "hooks")
    if target_dir:
        # Remove any .git directories that were possibly given by the user
        target_dir = os.path.join(target_dir.strip(hook_dir), hook_dir)
    else:
        try:
            git_root = check_output(["git", "rev-parse", "--show-toplevel"])
            git_root = git_root.decode(sys.stdout.encoding).rstrip()
        except CalledProcessError as exc:
            raise InstallException("Could not determine git root directory") from exc
        target_dir = os.path.join(git_root, hook_dir)
        print(target_dir)
    if not os.path.isdir(target_dir):
        raise InstallException("Target directory does not contain a '.git' folder")
    return target_dir


def get_umask():
    umask = os.umask(0)
    os.umask(umask)
    return umask


def chmod_plus_x(path):
    os.chmod(
        path,
        os.stat(path).st_mode
        | ((stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH) & ~get_umask()),
    )


@click.command()
@click.option("--target-dir", default="", help="Target directory to install git hooks.")
def install_hooks(target_dir: str) -> None:
    source_dir = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
    target_dir = os.path.abspath(get_target_dir(target_dir))
    for file in HOOK_FILES:
        try:
            target_file = os.path.join(target_dir, file)
            source_file = os.path.join(source_dir, file)
            if os.path.isfile(target_file):
                print(
                    f"Backing existing git hook file [{file}] up to [{file + BACKUP_EXT}]"
                )
                shutil.move(target_file, target_file + BACKUP_EXT)
            print(f"Installing git hook file [{file}]")
            shutil.copyfile(source_file, target_file)
            chmod_plus_x(target_file)
        except KeyboardInterrupt:
            print("Abort by keyboard interrupt")
            sys.exit(1)
        except OSError:
            print(f"Exception occurred during copying of file [{file}]")
    sys.exit(0)


if __name__ == "__main__":
    install_hooks()
