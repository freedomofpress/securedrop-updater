#!/bin/bash

set -e
set -u
set -o pipefail

source "$(dirname "$0")/common.sh"

# Install Qubes OS repo because we depend on qubes packages
sudo cp "${TOPLEVEL}/bootstrap/qubes-dom0.repo" /etc/yum.repos.d/
sudo cp "${TOPLEVEL}/bootstrap/RPM-GPG-KEY-qubes-4.1-primary" /etc/pki/rpm-gpg/

"${TOPLEVEL}/scripts/build-rpm.sh"

sudo mkdir -p "/var/lib/${PROJECT}"
echo "0.0.0" | sudo tee "/var/lib/${PROJECT}/version" > /dev/null

sudo mkdir -p "/usr/libexec/${PROJECT}/migrations/"
sed '1,/exit\ /d' <<<"$(cat "$0")" | sed 's/.\(.*\)/\1/' | sudo tee "/usr/libexec/${PROJECT}/migrations/0.1.0.py" > /dev/null
sudo chmod +x "/usr/libexec/${PROJECT}/migrations/0.1.0.py"


cd "${TOPLEVEL}/rpm-build/RPMS/noarch/"
# Install dependencies first so that we can see failures without having to
# scroll forever
dnf repoquery --deplist ./* | grep -oP '(?<=provider: ).+(?=-.+-[0-9]+\.fc[0-9]{2})' | sort -u | xargs sudo dnf install -y

# Install
sudo dnf install -y ./*

# Have migrations created the expected file?
grep lol < /lol
exit $?
##!/usr/bin/python3
#"""
#Super dirty way to inject a migration script on the fly, this is WIP and this
#whole bash script will be replaced by a more robust pytest environment
#"""
#
#import os
#from steps import MigrationStep, migrate
#
#
#class LolFile(MigrationStep):
#    def __init__(self, full_path):
#        self.full_path = full_path
#
#    def run(self):
#        with open(self.full_path, "w") as lol:
#            lol.write("lol\n")
#
#    def revert(self):
#        if os.path.exists(self.full_path):
#            os.remove(self.full_path)
#
#
#if __name__ == "__main__":
#    migrate(
#        [
#            LolFile("/lol"),
#        ]
#    )
