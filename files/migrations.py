#!/usr/bin/python3
"""
Runs migration scripts for this project

Intended to be triggered by the %post rpm scriptlet rather than manually.
"""

import logging
import subprocess
import sys
from pathlib import Path

from systemd.journal import JournalHandler

log = logging.getLogger("securedrop-updater-migrations")
log.addHandler(JournalHandler(SYSLOG_IDENTIFIER="securedrop-updater-migrations"))
log.setLevel(logging.INFO)


class Version:
    """
    A sortable software version

    Reads version strings, and sorts by major.minor.patch[.etc[.etc …]]
    """

    def __init__(self, version):
        """
        Read version numbers into lists of ints, discard anything that comes
        after the first character that is neither a period or a digit
        """
        chunks = []
        # Opting for minimal code over execution speed
        for part in version.split("."):
            digits = ""
            for char in part.split():
                if char.isdigit():
                    digits += char
                else:
                    # Treat RCs, betas etc. as if it were the full release
                    break
            chunks.append(int(digits))
        self.version = tuple(chunks)

    def __str__(self):
        return ".".join(str(v) for v in self.version)


class Migration(Version):
    """
    A sortable runnable migration

    Subclass of Version so that we can sort migrations just as easily as version strings
    """

    def __init__(self, path):
        super().__init__(path.name.rsplit(".", 1)[0])
        self.path = path

    def run_and_update_version_file(self, version_file):
        """
        Run this migration
        """
        rc = None
        try:
            log.info(f"Running migration for {self}")
            process = subprocess.Popen([str(self.path)])
            stdout, stderr = process.communicate()
            if stdout:
                log.info(stdout)
            if stderr:
                log.error(stderr)
            rc = process.returncode
        except subprocess.CalledProcessError as error:
            log.error(f"{error}", file=sys.stderr)

        if rc != 0:
            sys.exit(2)

        # If we successfully ran the migration, we are now in a new state that we want to see
        # reflected in case a subsequent migration fails
        update_version(self, version_file)


def update_version(target, version_file):
    version_file.write_text(f"{target}")


if __name__ == "__main__":
    PROJECT = sys.argv[1]
    VERSION_FILE = Path(f"/var/lib/{PROJECT}/version")
    MIGRATIONS_DIR = Path(f"/usr/libexec/{PROJECT}/migrations/")
    ACTION = int(sys.argv[2])
    VERSION_TARGET = Version(sys.argv[3])

    if VERSION_FILE.exists():
        with VERSION_FILE.open("r") as version:
            VERSION_BASE = Version(version.read().strip())
    # ACTION: 1: install, 2: upgrade
    elif ACTION == 1:
        # See https://docs.fedoraproject.org/en-US/packaging-guidelines/Scriptlets/#_syntax
        update_version(VERSION_TARGET, VERSION_FILE)
        sys.exit(0)
    else:
        log.error(f"Aborting: cannot upgrade without version file: '{VERSION_FILE}'")
        sys.exit(2)

    # The following glob implies that no Python file names in this folder may end in a number except
    # migrations named after the version of the state that they establish.
    migrations = sorted(
        [Migration(p) for p in MIGRATIONS_DIR.glob("*[0-9].py")], key=lambda m: m.version
    )

    for migration in migrations:
        if VERSION_BASE.version < migration.version <= VERSION_TARGET.version:
            migration.run_and_update_version_file(VERSION_FILE)
