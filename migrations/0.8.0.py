"""
SecureDrop Update migration to version 0.8.0
"""

import grp
import os
import pwd
import shutil
from pathlib import Path

from migration_steps import Absent, MigrationStep, Move, Symlink, path_rollback, path_snapshot


class DesktopFile(MigrationStep):
    def __init__(self, path: Path, gui_user_path: Path, uid: int, gid: int) -> None:
        self.path = path
        self.gui_user_path = gui_user_path
        self.target = self.gui_user_path / "Desktop" / self.path.name
        self.uid = uid
        self.gid = gid

    def run(self) -> None:
        shutil.copy2(self.path, self.target)
        os.chown(self.target, self.uid, self.gid, follow_symlinks=False)
        self.target.chmod(0o755)

    def rollback(self, _tmpdir: Path) -> None:
        if self.target.exists():
            self.target.unlink()


class RemoveCronJob(MigrationStep):
    def __init__(self, crontab: Path) -> None:
        self.path = crontab

    def snapshot(self, tmpdir: Path) -> None:
        path_snapshot(self.path, tmpdir)

    def run(self) -> None:
        clean = ""
        buffer = ""

        SEEKING = 1
        BEGIN = 2
        MATCHED = 3
        END = 4
        state = SEEKING

        error = Exception("Didn't find the expected sdw-notify block - modified crontab?")

        for line in self.path.open().readlines():
            if state == END:
                clean += line
            elif state == MATCHED and "### END securedrop-workstation ###" in line:
                state = END
            elif state == MATCHED:
                raise error
            elif state == BEGIN and "/opt/securedrop/launcher/sdw-notify.py" in line:
                state = MATCHED
            elif state == BEGIN:
                clean += buffer
                clean += line
                buffer = ""
                state = SEEKING
            elif state == SEEKING and "### BEGIN securedrop-workstation ###" in line:
                buffer += line
                state = BEGIN
            elif state == SEEKING:
                clean += line
        if state == END:
            raise error

        self.path.open("w").write(clean)

    def rollback(self, tmpdir: Path):
        path_rollback(self.path, tmpdir)


class EnableSystemdUserTimer(MigrationStep):
    def __init__(self, gui_user: str) -> None:
        self.gui_user = gui_user

    def run(self) -> None:
        os.popen("systemctl daemon-reload")
        os.popen(f"su -c 'systemctl --user enable sdw-notify.timer --now' {self.gui_user}")  # nosec


# Based on securedrop-workstation:dom0/sd-dom0-files.sls#L113
# blob eea04b9443715c587acbed716639ebc1869bc748
GUI_USER = grp.getgrnam("qubes").gr_mem[0]
GUI_USER_HOME = Path(os.path.expanduser(f"~{GUI_USER}"))
GUI_USER_PW = pwd.getpwnam(GUI_USER)
GUI_USER_UID = GUI_USER_PW.pw_uid
GUI_USER_GID = GUI_USER_PW.pw_gid

DESKTOP_FILE_NAME = "press.freedom.SecureDropUpdater.desktop"
APPLICATION_PATH = Path("/usr/share/applications/")

steps = [
    Absent(GUI_USER_HOME / "Desktop" / "securedrop-launcher.desktop"),
    Absent(GUI_USER_HOME / ".config" / "autostart" / "SDWLogin.desktop"),
    Move(GUI_USER_HOME / ".securedrop_launcher", GUI_USER_HOME / ".securedrop_updater"),
    Symlink(
        APPLICATION_PATH / DESKTOP_FILE_NAME,
        GUI_USER_HOME / ".config" / "autostart" / DESKTOP_FILE_NAME,
    ),
    DesktopFile(APPLICATION_PATH / DESKTOP_FILE_NAME, GUI_USER_HOME, GUI_USER_UID, GUI_USER_GID),
    RemoveCronJob(Path("/etc/crontab")),
    EnableSystemdUserTimer(GUI_USER),
]
