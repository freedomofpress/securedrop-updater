#!/bin/bash

set -e
set -u
set -o pipefail

source "$(dirname "$0")/common.sh"

"${TOPLEVEL}/scripts/build-rpm.sh"
cd "${TOPLEVEL}/rpm-build/RPMS/noarch/"

sudo mkdir -p "/var/lib/${PROJECT}"
echo "0.0.0" | sudo tee "/var/lib/${PROJECT}/version" > /dev/null

sudo mkdir -p "/usr/libexec/${PROJECT}/migrations/"
echo -e "#!/bin/bash\necho lol > /lol" | sudo tee "/usr/libexec/${PROJECT}/migrations/0.1.0.sh" > /dev/null
sudo chmod +x "/usr/libexec/${PROJECT}/migrations/0.1.0.sh"

# Install dependencies first so that we can see failures without having to
# scroll forever
dnf repoquery --deplist ./* | grep -oP '(?<=provider: ).+(?=-.+-[0-9]+\.fc[0-9]{2})' | sort -u | xargs sudo dnf install -y

# Install
sudo dnf install -y ./*

# Have migrations created the expected file?
grep lol < /lol
