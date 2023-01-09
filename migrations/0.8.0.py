#!/usr/bin/python3
"""
SecureDrop Update migration to version 0.8.0
"""

import grp
import os
import pwd
import shutil
from pathlib import Path

from steps import MigrationStep, Move, Remove, Symlink, migrate


class DesktopFile(MigrationStep):
    def __init__(self, path, gui_user_path, uid, gid):
        self.path = Path(path)
        self.gui_user_path = Path(gui_user_path)
        self.target = self.gui_user_path / "Desktop" / self.path.name
        self.uid = uid
        self.gid = gid

    def run(self):
        shutil.copy2(str(self.path), str(self.target))
        os.chown(str(self.target), self.uid, self.gid, follow_symlinks=False)
        self.target.chmod(0o755)

    def revert(self, _tmpdir):
        if self.target.exists():
            self.target.unlink()


if __name__ == "__main__":
    # Based on securedrop-workstation:dom0/sd-dom0-files.sls#L113
    # blob eea04b9443715c587acbed716639ebc1869bc748
    GUI_USER = grp.getgrnam("qubes").gr_mem[0]
    GUI_USER_HOME = os.path.expanduser(f"~{GUI_USER}")
    GUI_USER_PW = pwd.getpwnam(GUI_USER)
    GUI_USER_UID = GUI_USER_PW.pw_uid
    GUI_USER_GID = GUI_USER_PW.pw_gid

    DESKTOP_FILE_NAME = "press.freedom.SecureDropUpdater.desktop"
    APPLICATION_PATH = "/usr/share/applications/"

    migrate(
        [
            Remove(f"{GUI_USER_HOME}/Desktop/securedrop-launcher.desktop", True),
            Remove(f"{GUI_USER_HOME}/.config/autostart/SDWLogin.desktop", True),
            Move(f"{GUI_USER_HOME}/.securedrop_launcher", f"{GUI_USER_HOME}/.securedrop_updater"),
            Symlink(
                f"{APPLICATION_PATH}{DESKTOP_FILE_NAME}",
                f"{GUI_USER_HOME}/.config/autostart/{DESKTOP_FILE_NAME}",
            ),
            DesktopFile(
                f"{APPLICATION_PATH}{DESKTOP_FILE_NAME}", GUI_USER_HOME, GUI_USER_UID, GUI_USER_GID
            ),
        ]
    )
