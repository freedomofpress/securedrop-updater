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

# Install
sudo dnf install -y ./*

grep lol < /lol
