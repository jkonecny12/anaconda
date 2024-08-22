#!/bin/bash
#
# Anaconda has plenty of dependencies and because of that it's hard to set
# environment to with Anaconda properly.
# Run this script to install all the required dependencies for the autotools to be
# able to call make commands. This will enable you to test anaconda more easily.
#
# To avoid messing your system feel free to use `toolbox` in fedora so all the
# dependencies will be installed to the container instead of your system.
# The toolbox package is in standard Fedora repository.
#
# For toolbox use case run:
#
#   $ toolbox create
#   $ toolbox enter
#   $ sudo ./scripts/testing/install_dependencies.sh
#
#
# For direct host installation run:
#
#   $ sudo ./scripts/testing/install_dependencies.sh
#
#
# You can also pass any additional parameters for dnf. To make installation
# non-interactive you can call:
#
#   $ sudo ./scripts/testing/install_dependencies.sh -y

set -eu

# shellcheck disable=SC2068
dnf install $@ make rpm-build python3-polib

TEMP=$(mktemp /tmp/anaconda.spec.XXXXXXX)

# remove all problematic pieces from anaconda spec to be able to get dependencies
sed 's/@PACKAGE_VERSION@/0/; s/@PACKAGE_RELEASE@/0/; s/%{__python3}/python3/' ./anaconda.spec.in > $TEMP

# get all build requires dependencies from the spec file and strip out version
# version could be problematic because of fedora version you are running and
# they are mostly not important for automake
build_deps=$(rpmspec -q --buildrequires $TEMP | sed 's/>=.*$//')
# add also runtime dependencies for the local development
# remove anaconda packages and also '(glibc-langpack-en or glibc-all-langpacks)' which will fail otherwise
# list all the package which doesn't help with development and just making the developer environment heavier
IGNORE_DEPS="\
-widgets \
anaconda- \
brltty \
btrfs-progs \
crypto-policies-scripts \
dbus-daemon \
dbus-x11 \
device-mapper-multipath \
dosfstools \
dracut \
e2fsprogs \
f2fs-tools \
fcoe-utils \
fedora-logos \
flatpak-libs \
gdb \
glade \
gnome-kiosk \
chrony \
iputils \
kbd \
NetworkManager \
NetworkManager-libnm \
NetworkManager-team \
NetworkManager-wifi \
nm-connection-editor \
nm-connection-editor \
ntfs-3g \
ntfsprogs \
nvme-cli \
ostree \
podman \
realmd \
rsync \
skopeo \
skopeo \
systemd \
systemd-resolved \
teamd \
tecla \
tmux \
udisks2-iscsi \
util-linux \
xfsprogs \
xisxwayland \
xorg-x11-driver \
xorg-x11-server-Xorg \
xrandr \
xrdb \
xz \
zenity \
zram-generator-defaults"

requires_deps=$(rpmspec -q --requires $TEMP | grep -v -E "(${IGNORE_DEPS// /|}| or )" | sed 's/>=.*$//')

# shellcheck disable=SC2068
dnf install $@ $build_deps $requires_deps  # do NOT quote the list or it falls apart

# clean up the temp file
rm $TEMP
