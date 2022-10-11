FROM fedora:32
LABEL org="Freedom of the Press"
LABEL image_name="securedrop-updater-qubes-4.1"

ARG USER_NAME
ENV USER_NAME ${USER_NAME:-root}
ARG USER_ID
ENV USER_ID ${USER_ID:-0}

RUN dnf install -y \
        git \
        make \
        file \
        python3-devel \
        python3-pip \
        python3-qt5 \
        xorg-x11-server-Xvfb \
        rpmdevtools \
        rpmlint \
        ShellCheck

COPY requirements requirements
RUN python3.8 -m venv --system-site-packages /opt/venvs/securedrop-updater && \
    /opt/venvs/securedrop-updater/bin/pip3 install --no-deps --require-hashes -r requirements/dev-requirements.txt

RUN if test $USER_NAME != root ; then useradd --no-create-home --home-dir /tmp --uid $USER_ID $USER_NAME && echo "$USER_NAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers ; fi

RUN curl https://raw.githubusercontent.com/QubesOS/qubes-qubes-release/master/qubes-dom0.repo.in | sed -e 's/$releasever/4.1/g' -e 's/%DIST%/fc32/g' > /etc/yum.repos.d/qubes-dom0.repo && \
    curl -o /etc/pki/rpm-gpg/RPM-GPG-KEY-qubes-4.1-primary https://raw.githubusercontent.com/QubesOS/qubes-qubes-release/master/RPM-GPG-KEY-qubes-4-primary

ENV PATH "/opt/venvs/securedrop-updater/bin/:$PATH"
