#!/usr/bin/python3
"""
SecureDrop Update migration to version 0.8.0
"""

import grp
import os
import pwd
import shutil

from steps import MigrationStep, Move, Remove, Symlink, migrate


class DesktopFile(MigrationStep):
    def __init__(self, full_path, gui_user_path, uid, gid):
        self.full_path = full_path
        self.gui_user_path = gui_user_path
        self.desktop_file_name = os.path.basename(full_path)
        self.full_path_desktop = f"{self.gui_user_path}/Desktop/{self.desktop_file_name}"
        self.uid = uid
        self.gid = gid

    def run(self):
        shutil.copy2(self.full_path, self.full_path_desktop)
        os.chown(self.full_path_desktop, self.uid, self.gid, follow_symlinks=False)
        os.chmod(self.full_path_desktop, 0o755, follow_symlinks=False)  # nosec

    def revert(self, _tmpdir):
        if os.path.exists(self.full_path_desktop):
            os.remove(self.full_path_desktop)


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
