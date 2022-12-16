#!/usr/bin/python3
"""
Runs migration scripts for this project

Intended to be triggered by the %post rpm scriptlet rather than manually.
"""

import os
import subprocess
import sys
from glob import glob

VERSION_FILE = "/var/lib/{}/version"
MIGRATIONS_DIR = "/usr/libexec/{}/migrations/"


class Version:
    """
    A sortable software version

    Reads version strings, and sorts by major.minor.patch[.etc[.etc …]]
    """

    def __init__(self, version, delim="."):
        """
        Read version numbers into lists of ints, discard anything that comes
        after the first character that is neither a period or a digit
        """
        self.version = []
        # Opting for minimal code over execution speed
        for part in version.split(delim):
            digits = ""
            for char in part.split():
                if char.isdigit():
                    digits += char
                else:
                    # Treat RCs, betas etc. as if it were the full release
                    break
            self.version.append(int(digits))

    def __lt__(self, other):
        """
        This method assumes that adding another digit is another release
        that's newer than the one without
        """
        cmp = []
        for i in range(min(len(self.version), len(other.version))):
            cmp.append((other.version[i] > self.version[i]) - (other.version[i] < self.version[i]))
        for sub in cmp:
            if sub != 0:
                return bool(sub + 1)
        if len(other.version) > len(self.version):
            return True
        return False

    def __eq__(self, other):
        return self.version == other.version

    def __le__(self, other):
        if self == other:
            return True
        return self < other


class Migration(Version):
    """
    A sortable runnable migration

    Subclass of Version so that we can sort migrations just as easily as version strings
    """

    def __init__(self, file_name):
        super().__init__(file_name.rsplit(".", 1)[0])
        self.file_name = file_name

    def run(self):
        """
        Run this migration
        """
        try:
            print(f"Running migration for {self.version}")
            subprocess.Popen([f"./{self.file_name}"]).wait()
        except subprocess.CalledProcessError as error:
            print(f"{error}", file=sys.stderr)
            sys.exit(1)


def update_version(target):
    with open(VERSION_FILE, "w+", encoding="utf-8") as ver:
        ver.write(f"{target}")


if __name__ == "__main__":
    PROJECT = sys.argv[1]
    VERSION_FILE = VERSION_FILE.format(PROJECT)
    MIGRATIONS_DIR = MIGRATIONS_DIR.format(PROJECT)
    ACTION = int(sys.argv[2])
    VERSION_TARGET = Version(sys.argv[3])

    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, "r", encoding="utf-8") as version_file:
            VERSION_BASE = Version(version_file.read().strip())
    # ACTION: 1: install, 2: upgrade
    elif ACTION == 1:
        # See https://docs.fedoraproject.org/en-US/packaging-guidelines/Scriptlets/#_syntax
        update_version(VERSION_TARGET)
        sys.exit(0)
    else:
        print(f"Aborting: cannot upgrade without version file: '{VERSION_FILE}'", file=sys.stderr)
        sys.exit(1)

    os.chdir(MIGRATIONS_DIR)
    migrations = sorted([Migration(file_name) for file_name in glob("*")])

    for migration in migrations:
        if VERSION_BASE < migration <= VERSION_TARGET:
            migration.run()

    # Successfully ran all migrations!
    update_version(VERSION_TARGET)
