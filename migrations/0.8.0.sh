#!/bin/bash
# SecureDrop Update migration to version 0.8.0

DESKTOP_FILE="press.freedom.SecureDropUpdater.desktop"
APP_PATH="/usr/share/applications/"

# See https://github.com/freedomofpress/securedrop-workstation/blob/eea04b9443715c587acbed716639ebc1869bc748/dom0/sd-dom0-files.sls#L113
GUI_USER="$(groupmems -l -g qubes)"
GUI_USER_HOME=$(getent passwd "${GUI_USER}" | cut -d: -f6)

# Remove bits and bobs we don't want/need anymore

rm "${GUI_USER_HOME}/Desktop/securedrop-launcher.desktop"
rm "${GUI_USER_HOME}/.config/autostart/SDWLogin.desktop"

cp "${APP_PATH}${DESKTOP_FILE}" "${GUI_USER_HOME}/Desktop/"
chmod 755 "$GUI_USER:$GUI_USER" "${GUI_USER_HOME}/Desktop/${DESKTOP_FILE}"
ln -s "${APP_PATH}${DESKTOP_FILE}" "${GUI_USER_HOME}/.config/autostart/"

mv "${GUI_USER_HOME}/.securedrop_launcher" "${GUI_USER_HOME}/.securedrop_updater"
