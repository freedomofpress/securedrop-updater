#!/bin/bash
set -e
set -u
set -o pipefail

source "$(dirname "$0")/common.sh"

echo Building RPM, first pass
"$(dirname "$0")/build-rpm.sh"
cp "rpm-build/RPMS/noarch/${PROJECT}-$(cat "${TOPLEVEL}/VERSION")"*.rpm /tmp/
echo Building RPM, second pass
"$(dirname "$0")/build-rpm.sh"
echo Comparing builds with diffoscope
TERM=xterm-256color diffoscope "rpm-build/RPMS/noarch/${PROJECT}-$(cat "${TOPLEVEL}/VERSION")"*.rpm "/tmp/${PROJECT}-$(cat "${TOPLEVEL}/VERSION")"*.rpm && \
    echo Success!
