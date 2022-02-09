"""overrides.py: overrides for various functions"""
#
# Copyright (C) 2017-2018 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

#
# sr_lint.py overrides
#
# To be removed. For now we know that snap names have a 1 to 1 mapping
# to publishers so we can whitelist snap names for snap types to not
# flag for manual review.
# NOTE: this will eventually move to assertions
redflagged_snap_types_overrides = {
    "kernel": [
        "dragonboard-kernel",  # Canonical reference kernels
        "pc-kernel",
        "pi-kernel",
        "pi2-kernel",
        "aws-kernel",  # @canonical.com kernels
        "azure-kernel",
        "freescale-ls1043a-kernel",
        "gcp-kernel",
        "gke-kernel",
        "hummingboard-kernel",
        "intel-kernel",
        "intel-iotg-kernel",
        "iot-kernel",
        "joule-drone-kernel",
        "joule-linux",
        "joule-linux-lool",
        "linux-generic-allwinner",
        "mako-kernel",
        "marvell-armada3700-kernel",
        "mediatek-aiot-kernel",
        "nitrogen6x-kernel",
        "nxp-ls1043a-kernel",
        "odroidxu4-kernel",
        "pc-lowlatency-kernel",
        "pi2-kernel-rt",
        "rockpro64-kernel",
        "roseapple-pi-kernel",
        "roseapple-pi-kernel-ondra",
        "artik5-linux",  # 3rd party vendor kernels
        "artik10-linux",
        "bubblegum96-kernel",
        "eragon410-kernel",
        "linux-generic-bbb",
        "rexroth-xm21-kernel",
        "nitrogen-kernel",
        "teal-kernel",
        "telig-kernel",
        "tsimx6-kernel",
    ],
    "os": ["core", "ubuntu-core"],
    "gadget": [
        "cm3",  # Canonical reference gadgets
        "dragonboard",
        "pc",
        "pi",
        "pi2",
        "pi3",
        "cm3-ondra",  # @canonical.com gadgets
        "cm3-openhab",
        "cubox-i",
        "hikey-snappy-gadget",
        "hummingboard",
        "joule",
        "mediatek-aiot",
        "nanopi-air",
        "nanopi-neo",
        "nxp-ls1043ardb-gadget",
        "odroid-xu4",
        "orangepi-zero",
        "orangepi-zero-ogra",
        "pi-kiosk",
        "pi3-ondra",
        "pi3-openhab",
        "pi3-unipi",
        "pi2kyle",
        "pi3testbootsplash",
        "pocketbeagle",
        "rockpro64-gadget",
        "roseapple-pi",
        "sabrelite",
        "wdl-nextcloud",
        "wdl-nextcloud-pi2",
        "artik5",  # 3rd party vendor and brand store gadgets
        "artik10",
        "bubblegum96-gadget",
        "dragonboard-turtlebot-kyrofa",
        "eragon410",
        "eragon-sunny",
        "lemaker-guitar-gadget",
        "nitrogen-gadget",
        "pc-turtlebot-kyrofa",
        "rexroth-xm21",
        "screenly-gadget-pi3",
        "screenly-gadget-resin-rubus",
        "screenly-gadget-cm3",
        "subutai-pc",
        "telig",
        "tsimx6-gadget",
    ],
    "base": [
        "bare",  # Canonical base snaps
        "base-18",
        "core16",
        "core18",
        "core20",
        "core22",
        "test-snapd-base",
        "test-snapd-core18",
        "fedora29",  # Community base snaps
        "freedesktop-sdk-runtime-2008",
        "godot-bare",
        "nix-base",
        "solus-runtime-gaming",
    ],
    "snapd": ["snapd"],
}

# List of snaps that may specify an interface that requires a desktop file but
# not supply a desktop file itself.
desktop_file_exception = ["emoj", "ffscreencast", "pulsemixer"]

# List of classic snaps that may specify slots/plugs (eg, for workaround
# content interface methodology)
classic_interfaces_exception = ["certbot", "juju", "microk8s", "eks", "xlnx-config"]

# List additional attributes that a particular snap may specify with a
# particular side of a particular interface (eg, for workaround content
# interface methodology)
interfaces_attribs_addons = {"microk8s": {"content": {"name/slots": ""}}}

#
# sr_security.py overrides
#
# Files with unusual modes that we'll allow for certain snaps.
# NOTE: when SNAP_FAKEROOT_RESQUASHFS=0 adding setuid/setgid files here
# will disable resquash enforcement. Format:
#   <pkgname>: {<fname>: <mode>},
#   <pkgname2>: {<fname2>: [<mode2>, <mode3>]}
sec_mode_overrides = {
    "bare": {},
    "base-18": {
        "./bin/mount": "rwsr-xr-x",
        "./bin/su": "rwsr-xr-x",
        "./bin/umount": "rwsr-xr-x",
        "./sbin/pam_extrausers_chkpwd": "rwxr-sr-x",
        "./sbin/unix_chkpwd": "rwxr-sr-x",
        "./tmp": "rwxrwxrwt",
        "./usr/bin/chage": "rwxr-sr-x",
        "./usr/bin/chfn": "rwsr-xr-x",
        "./usr/bin/chsh": "rwsr-xr-x",
        "./usr/bin/expiry": "rwxr-sr-x",
        "./usr/bin/gpasswd": "rwsr-xr-x",
        "./usr/bin/newgrp": "rwsr-xr-x",
        "./usr/bin/passwd": "rwsr-xr-x",
        "./usr/bin/ssh-agent": "rwxr-sr-x",
        "./usr/bin/sudo": "rwsr-xr-x",
        "./usr/bin/wall": "rwxr-sr-x",
        "./usr/lib/dbus-1.0/dbus-daemon-launch-helper": "rwsr-xr--",
        "./usr/lib/openssh/ssh-keysign": "rwsr-xr-x",
        "./var/local": "rwxrwsr-x",
        "./var/mail": "rwxrwsr-x",
        "./var/tmp": "rwxrwxrwt",
    },
    "chrome-test": {  # chrome-test from Canonical
        "./opt/google/chrome/chrome-sandbox": "rwsr-xr-x"
    },
    "chromium": {  # chromium from Canonical
        "./usr/lib/chromium-browser/chrome-sandbox": "r-sr-xr-x"
    },
    "chromium-mir-kiosk": {  # chromium from Canonical with XWayland, etc
        "./usr/lib/chromium-browser/chrome-sandbox": "r-sr-xr-x"
    },
    "core": {
        "./bin/mount": "rwsr-xr-x",
        "./bin/ping": "rwsr-xr-x",
        "./bin/ping6": "rwsr-xr-x",
        "./bin/su": "rwsr-xr-x",
        "./bin/umount": "rwsr-xr-x",
        "./etc/chatscripts": "rwxr-s---",
        "./etc/ppp/peers": "rwxr-s---",
        "./run/lock": "rwxrwxrwt",
        "./sbin/pam_extrausers_chkpwd": "rwxr-sr-x",
        "./sbin/unix_chkpwd": "rwxr-sr-x",
        "./tmp": "rwxrwxrwt",
        "./usr/bin/chage": "rwxr-sr-x",
        "./usr/bin/chfn": "rwsr-xr-x",
        "./usr/bin/chsh": "rwsr-xr-x",
        "./usr/bin/crontab": "rwxr-sr-x",
        "./usr/bin/dotlockfile": "rwxr-sr-x",
        "./usr/bin/expiry": "rwxr-sr-x",
        "./usr/bin/gpasswd": "rwsr-xr-x",
        "./usr/bin/mail-lock": "rwxr-sr-x",
        "./usr/bin/mail-unlock": "rwxr-sr-x",
        "./usr/bin/mail-touchlock": "rwxr-sr-x",
        "./usr/bin/newgrp": "rwsr-xr-x",
        "./usr/bin/passwd": "rwsr-xr-x",
        "./usr/bin/ssh-agent": "rwxr-sr-x",
        "./usr/bin/sudo": "rwsr-xr-x",
        "./usr/bin/wall": "rwxr-sr-x",
        "./usr/lib/dbus-1.0/dbus-daemon-launch-helper": "rwsr-xr--",
        "./usr/lib/openssh/ssh-keysign": "rwsr-xr-x",
        "./usr/lib/snapd/snap-confine": ["rwsr-sr-x", "rwsr-xr-x"],
        "./usr/local/lib/python3.5": "rwxrwsr-x",
        "./usr/local/lib/python3.5/dist-packages": "rwxrwsr-x",
        "./usr/sbin/pppd": "rwsr-xr--",
        "./var/local": "rwxrwsr-x",
        "./var/mail": "rwxrwsr-x",
        "./var/spool/cron/crontabs": "rwx-wx--T",
        "./var/tmp": "rwxrwxrwt",
    },
    "core16": {
        "./bin/mount": "rwsr-xr-x",
        "./bin/ping": "rwsr-xr-x",
        "./bin/ping6": "rwsr-xr-x",
        "./bin/su": "rwsr-xr-x",
        "./bin/umount": "rwsr-xr-x",
        "./etc/chatscripts": "rwxr-s---",
        "./etc/ppp/peers": "rwxr-s---",
        "./run/lock": "rwxrwxrwt",
        "./sbin/pam_extrausers_chkpwd": "rwxr-sr-x",
        "./sbin/unix_chkpwd": "rwxr-sr-x",
        "./tmp": "rwxrwxrwt",
        "./usr/bin/chage": "rwxr-sr-x",
        "./usr/bin/chfn": "rwsr-xr-x",
        "./usr/bin/chsh": "rwsr-xr-x",
        "./usr/bin/crontab": "rwxr-sr-x",
        "./usr/bin/dotlockfile": "rwxr-sr-x",
        "./usr/bin/expiry": "rwxr-sr-x",
        "./usr/bin/gpasswd": "rwsr-xr-x",
        "./usr/bin/mail-lock": "rwxr-sr-x",
        "./usr/bin/mail-unlock": "rwxr-sr-x",
        "./usr/bin/mail-touchlock": "rwxr-sr-x",
        "./usr/bin/newgrp": "rwsr-xr-x",
        "./usr/bin/passwd": "rwsr-xr-x",
        "./usr/bin/ssh-agent": "rwxr-sr-x",
        "./usr/bin/sudo": "rwsr-xr-x",
        "./usr/bin/wall": "rwxr-sr-x",
        "./usr/lib/dbus-1.0/dbus-daemon-launch-helper": "rwsr-xr--",
        "./usr/lib/openssh/ssh-keysign": "rwsr-xr-x",
        "./usr/lib/snapd/snap-confine": "rwsr-sr-x",
        "./usr/local/lib/python3.5": "rwxrwsr-x",
        "./usr/local/lib/python3.5/dist-packages": "rwxrwsr-x",
        "./usr/sbin/pppd": "rwsr-xr--",
        "./var/local": "rwxrwsr-x",
        "./var/mail": "rwxrwsr-x",
        "./var/spool/cron/crontabs": "rwx-wx--T",
        "./var/tmp": "rwxrwxrwt",
    },
    "core18": {
        "./bin/mount": "rwsr-xr-x",
        "./bin/ping": "rwsr-xr-x",
        "./bin/su": "rwsr-xr-x",
        "./bin/umount": "rwsr-xr-x",
        "./sbin/pam_extrausers_chkpwd": "rwxr-sr-x",
        "./sbin/unix_chkpwd": "rwxr-sr-x",
        "./tmp": "rwxrwxrwt",
        "./usr/bin/chage": "rwxr-sr-x",
        "./usr/bin/chfn": "rwsr-xr-x",
        "./usr/bin/chsh": "rwsr-xr-x",
        "./usr/bin/expiry": "rwxr-sr-x",
        "./usr/bin/gpasswd": "rwsr-xr-x",
        "./usr/bin/newgrp": "rwsr-xr-x",
        "./usr/bin/passwd": "rwsr-xr-x",
        "./usr/bin/ssh-agent": "rwxr-sr-x",
        "./usr/bin/sudo": "rwsr-xr-x",
        "./usr/bin/wall": "rwxr-sr-x",
        "./usr/lib/dbus-1.0/dbus-daemon-launch-helper": "rwsr-xr--",
        "./usr/lib/openssh/ssh-keysign": "rwsr-xr-x",
        "./var/local": "rwxrwsr-x",
        "./var/mail": "rwxrwsr-x",
        "./var/tmp": "rwxrwxrwt",
    },
    "core20": {
        "./usr/bin/mount": "rwsr-xr-x",
        "./bin/ping": "rwsr-xr-x",
        "./usr/bin/su": "rwsr-xr-x",
        "./usr/bin/umount": "rwsr-xr-x",
        "./usr/sbin/pam_extrausers_chkpwd": "rwxr-sr-x",
        "./usr/sbin/unix_chkpwd": "rwxr-sr-x",
        "./tmp": "rwxrwxrwt",
        "./usr/bin/chage": "rwxr-sr-x",
        "./usr/bin/chfn": "rwsr-xr-x",
        "./usr/bin/chsh": "rwsr-xr-x",
        "./usr/bin/expiry": "rwxr-sr-x",
        "./usr/bin/gpasswd": "rwsr-xr-x",
        "./usr/bin/newgrp": "rwsr-xr-x",
        "./usr/bin/passwd": "rwsr-xr-x",
        "./usr/bin/ssh-agent": "rwxr-sr-x",
        "./usr/bin/sudo": "rwsr-xr-x",
        "./usr/bin/wall": "rwxr-sr-x",
        "./usr/lib/dbus-1.0/dbus-daemon-launch-helper": "rwsr-xr--",
        "./usr/lib/openssh/ssh-keysign": "rwsr-xr-x",
        "./var/local": "rwxrwsr-x",
        "./var/mail": "rwxrwsr-x",
        "./var/tmp": "rwxrwxrwt",
    },
    "core22": {
        "./usr/bin/chage": "rwxr-sr-x",
        "./usr/bin/chfn": "rwsr-xr-x",
        "./usr/bin/chsh": "rwsr-xr-x",
        "./usr/bin/expiry": "rwxr-sr-x",
        "./usr/bin/gpasswd": "rwsr-xr-x",
        "./usr/bin/mount": "rwsr-xr-x",
        "./usr/bin/newgrp": "rwsr-xr-x",
        "./usr/bin/passwd": "rwsr-xr-x",
        "./usr/bin/ssh-agent": "rwxr-sr-x",
        "./usr/bin/su": "rwsr-xr-x",
        "./usr/bin/sudo": "rwsr-xr-x",
        "./usr/bin/umount": "rwsr-xr-x",
        "./usr/bin/wall": "rwxr-sr-x",
        "./usr/lib/dbus-1.0/dbus-daemon-launch-helper": "rwsr-xr--",
        "./usr/lib/openssh/ssh-keysign": "rwsr-xr-x",
        "./usr/sbin/pam_extrausers_chkpwd": "rwxr-sr-x",
        "./usr/sbin/unix_chkpwd": "rwxr-sr-x",
        "./var/mail": "rwxrwsr-x",
    },
    "openwrt": {"./rootfs/tmp": "rwxrwxrwt"},  # demo from Canonical
    "opera": {  # official Opera snap
        "./usr/lib/x86_64-linux-gnu/opera/opera_sandbox": "rwsr-xr-x"
    },
    "opera-beta": {  # official Opera snap
        "./usr/lib/x86_64-linux-gnu/opera-beta/opera_sandbox": "rwsr-xr-x"
    },
    "opera-developer": {  # official Opera snap
        "./usr/lib/x86_64-linux-gnu/opera-developer/opera_sandbox": "rwsr-xr-x"
    },
    "snapd": {"./usr/lib/snapd/snap-confine": ["rwsr-sr-x", "rwsr-xr-x"]},
    "skype": {"./usr/share/skypeforlinux/chrome-sandbox": "r-sr-xr-x"},
    "test-snapd-core18": {
        "./bin/mount": "rwsr-xr-x",
        "./bin/ping": "rwsr-xr-x",
        "./bin/su": "rwsr-xr-x",
        "./bin/umount": "rwsr-xr-x",
        "./sbin/pam_extrausers_chkpwd": "rwxr-sr-x",
        "./sbin/unix_chkpwd": "rwxr-sr-x",
        "./tmp": "rwxrwxrwt",
        "./usr/bin/chage": "rwxr-sr-x",
        "./usr/bin/chfn": "rwsr-xr-x",
        "./usr/bin/chsh": "rwsr-xr-x",
        "./usr/bin/expiry": "rwxr-sr-x",
        "./usr/bin/gpasswd": "rwsr-xr-x",
        "./usr/bin/newgrp": "rwsr-xr-x",
        "./usr/bin/passwd": "rwsr-xr-x",
        "./usr/bin/ssh-agent": "rwxr-sr-x",
        "./usr/bin/sudo": "rwsr-xr-x",
        "./usr/bin/wall": "rwxr-sr-x",
        "./usr/lib/dbus-1.0/dbus-daemon-launch-helper": "rwsr-xr--",
        "./usr/lib/openssh/ssh-keysign": "rwsr-xr-x",
        "./var/local": "rwxrwsr-x",
        "./var/mail": "rwxrwsr-x",
        "./var/tmp": "rwxrwxrwt",
    },
    "ubuntu-core": {
        "./bin/mount": "rwsr-xr-x",
        "./bin/ping": "rwsr-xr-x",
        "./bin/ping6": "rwsr-xr-x",
        "./bin/su": "rwsr-xr-x",
        "./bin/umount": "rwsr-xr-x",
        "./etc/chatscripts": "rwxr-s---",
        "./etc/ppp/peers": "rwxr-s---",
        "./run/lock": "rwxrwxrwt",
        "./sbin/pam_extrausers_chkpwd": "rwxr-sr-x",
        "./sbin/unix_chkpwd": "rwxr-sr-x",
        "./tmp": "rwxrwxrwt",
        "./usr/bin/chage": "rwxr-sr-x",
        "./usr/bin/chfn": "rwsr-xr-x",
        "./usr/bin/chsh": "rwsr-xr-x",
        "./usr/bin/crontab": "rwxr-sr-x",
        "./usr/bin/dotlockfile": "rwxr-sr-x",
        "./usr/bin/expiry": "rwxr-sr-x",
        "./usr/bin/gpasswd": "rwsr-xr-x",
        "./usr/bin/mail-lock": "rwxr-sr-x",
        "./usr/bin/mail-unlock": "rwxr-sr-x",
        "./usr/bin/mail-touchlock": "rwxr-sr-x",
        "./usr/bin/newgrp": "rwsr-xr-x",
        "./usr/bin/passwd": "rwsr-xr-x",
        "./usr/bin/ssh-agent": "rwxr-sr-x",
        "./usr/bin/sudo": "rwsr-xr-x",
        "./usr/bin/wall": "rwxr-sr-x",
        "./usr/lib/dbus-1.0/dbus-daemon-launch-helper": "rwsr-xr--",
        "./usr/lib/openssh/ssh-keysign": "rwsr-xr-x",
        "./usr/lib/snapd/snap-confine": "rwsr-xr-x",
        "./usr/local/lib/python3.5": "rwxrwsr-x",
        "./usr/local/lib/python3.5/dist-packages": "rwxrwsr-x",
        "./usr/sbin/pppd": "rwsr-xr--",
        "./var/local": "rwxrwsr-x",
        "./var/mail": "rwxrwsr-x",
        "./var/spool/cron/crontabs": "rwx-wx--T",
        "./var/tmp": "rwxrwxrwt",
    },
}

# bases shouldn't typically ship device files unless they are also functioning
# as an os snap. Format:
#   <pkgname>: {<fname>: (<ftype><mode>, <user>/<group>)},
#   <pkgname2>: {<fname2>: [(<ftype2><mode2>, <user2>/<group2>),
#                           (<ftype3><mode3>, <user3>/<group3>)]}
sec_mode_dev_overrides = {
    "base-18": {  # grandfathered
        "./dev/full": ("crw-rw-rw-", "0/0"),
        "./dev/null": ("crw-rw-rw-", "0/0"),
        "./dev/ptmx": ("crw-rw-rw-", "0/0"),
        "./dev/random": ("crw-rw-rw-", "0/0"),
        "./dev/tty": ("crw-rw-rw-", "0/0"),
        "./dev/urandom": ("crw-rw-rw-", "0/0"),
        "./dev/zero": ("crw-rw-rw-", "0/0"),
    },
    "core": {
        "./dev/agpgart": ("crw-rw----", "0/44"),
        "./dev/audio1": ("crw-rw----", "0/29"),
        "./dev/audio2": ("crw-rw----", "0/29"),
        "./dev/audio3": ("crw-rw----", "0/29"),
        "./dev/audio": ("crw-rw----", "0/29"),
        "./dev/audioctl": ("crw-rw----", "0/29"),
        "./dev/console": ("crw-------", "0/5"),
        "./dev/dsp1": ("crw-rw----", "0/29"),
        "./dev/dsp2": ("crw-rw----", "0/29"),
        "./dev/dsp3": ("crw-rw----", "0/29"),
        "./dev/dsp": ("crw-rw----", "0/29"),
        "./dev/full": ("crw-rw-rw-", "0/0"),
        "./dev/kmem": ("crw-r-----", "0/15"),
        "./dev/loop0": ("brw-rw----", "0/6"),
        "./dev/loop1": ("brw-rw----", "0/6"),
        "./dev/loop2": ("brw-rw----", "0/6"),
        "./dev/loop3": ("brw-rw----", "0/6"),
        "./dev/loop4": ("brw-rw----", "0/6"),
        "./dev/loop5": ("brw-rw----", "0/6"),
        "./dev/loop6": ("brw-rw----", "0/6"),
        "./dev/loop7": ("brw-rw----", "0/6"),
        "./dev/mem": ("crw-r-----", "0/15"),
        "./dev/midi00": ("crw-rw----", "0/29"),
        "./dev/midi01": ("crw-rw----", "0/29"),
        "./dev/midi02": ("crw-rw----", "0/29"),
        "./dev/midi03": ("crw-rw----", "0/29"),
        "./dev/midi0": ("crw-rw----", "0/29"),
        "./dev/midi1": ("crw-rw----", "0/29"),
        "./dev/midi2": ("crw-rw----", "0/29"),
        "./dev/midi3": ("crw-rw----", "0/29"),
        "./dev/mixer1": ("crw-rw----", "0/29"),
        "./dev/mixer2": ("crw-rw----", "0/29"),
        "./dev/mixer3": ("crw-rw----", "0/29"),
        "./dev/mixer": ("crw-rw----", "0/29"),
        "./dev/mpu401data": ("crw-rw----", "0/29"),
        "./dev/mpu401stat": ("crw-rw----", "0/29"),
        "./dev/null": ("crw-rw-rw-", "0/0"),
        "./dev/port": ("crw-r-----", "0/15"),
        "./dev/ram0": ("brw-rw----", "0/6"),
        "./dev/ram10": ("brw-rw----", "0/6"),
        "./dev/ram11": ("brw-rw----", "0/6"),
        "./dev/ram12": ("brw-rw----", "0/6"),
        "./dev/ram13": ("brw-rw----", "0/6"),
        "./dev/ram14": ("brw-rw----", "0/6"),
        "./dev/ram15": ("brw-rw----", "0/6"),
        "./dev/ram16": ("brw-rw----", "0/6"),
        "./dev/ram1": ("brw-rw----", "0/6"),
        "./dev/ram2": ("brw-rw----", "0/6"),
        "./dev/ram3": ("brw-rw----", "0/6"),
        "./dev/ram4": ("brw-rw----", "0/6"),
        "./dev/ram5": ("brw-rw----", "0/6"),
        "./dev/ram6": ("brw-rw----", "0/6"),
        "./dev/ram7": ("brw-rw----", "0/6"),
        "./dev/ram8": ("brw-rw----", "0/6"),
        "./dev/ram9": ("brw-rw----", "0/6"),
        "./dev/random": ("crw-rw-rw-", "0/0"),
        "./dev/rmidi0": ("crw-rw----", "0/29"),
        "./dev/rmidi1": ("crw-rw----", "0/29"),
        "./dev/rmidi2": ("crw-rw----", "0/29"),
        "./dev/rmidi3": ("crw-rw----", "0/29"),
        "./dev/sequencer": ("crw-rw----", "0/29"),
        "./dev/smpte0": ("crw-rw----", "0/29"),
        "./dev/smpte1": ("crw-rw----", "0/29"),
        "./dev/smpte2": ("crw-rw----", "0/29"),
        "./dev/smpte3": ("crw-rw----", "0/29"),
        "./dev/sndstat": ("crw-rw----", "0/29"),
        "./dev/tty0": ("crw-------", "0/5"),
        "./dev/tty1": ("crw-------", "0/5"),
        "./dev/tty2": ("crw-------", "0/5"),
        "./dev/tty3": ("crw-------", "0/5"),
        "./dev/tty4": ("crw-------", "0/5"),
        "./dev/tty5": ("crw-------", "0/5"),
        "./dev/tty6": ("crw-------", "0/5"),
        "./dev/tty7": ("crw-------", "0/5"),
        "./dev/tty8": ("crw-------", "0/5"),
        "./dev/tty9": ("crw-------", "0/5"),
        "./dev/tty": ("crw-rw-rw-", "0/5"),
        "./dev/urandom": ("crw-rw-rw-", "0/0"),
        "./dev/zero": ("crw-rw-rw-", "0/0"),
    },
    "core16": {
        "./dev/agpgart": ("crw-rw----", "0/44"),
        "./dev/audio1": ("crw-rw----", "0/29"),
        "./dev/audio2": ("crw-rw----", "0/29"),
        "./dev/audio3": ("crw-rw----", "0/29"),
        "./dev/audio": ("crw-rw----", "0/29"),
        "./dev/audioctl": ("crw-rw----", "0/29"),
        "./dev/console": ("crw-------", "0/5"),
        "./dev/dsp1": ("crw-rw----", "0/29"),
        "./dev/dsp2": ("crw-rw----", "0/29"),
        "./dev/dsp3": ("crw-rw----", "0/29"),
        "./dev/dsp": ("crw-rw----", "0/29"),
        "./dev/full": ("crw-rw-rw-", "0/0"),
        "./dev/kmem": ("crw-r-----", "0/15"),
        "./dev/loop0": ("brw-rw----", "0/6"),
        "./dev/loop1": ("brw-rw----", "0/6"),
        "./dev/loop2": ("brw-rw----", "0/6"),
        "./dev/loop3": ("brw-rw----", "0/6"),
        "./dev/loop4": ("brw-rw----", "0/6"),
        "./dev/loop5": ("brw-rw----", "0/6"),
        "./dev/loop6": ("brw-rw----", "0/6"),
        "./dev/loop7": ("brw-rw----", "0/6"),
        "./dev/mem": ("crw-r-----", "0/15"),
        "./dev/midi00": ("crw-rw----", "0/29"),
        "./dev/midi01": ("crw-rw----", "0/29"),
        "./dev/midi02": ("crw-rw----", "0/29"),
        "./dev/midi03": ("crw-rw----", "0/29"),
        "./dev/midi0": ("crw-rw----", "0/29"),
        "./dev/midi1": ("crw-rw----", "0/29"),
        "./dev/midi2": ("crw-rw----", "0/29"),
        "./dev/midi3": ("crw-rw----", "0/29"),
        "./dev/mixer1": ("crw-rw----", "0/29"),
        "./dev/mixer2": ("crw-rw----", "0/29"),
        "./dev/mixer3": ("crw-rw----", "0/29"),
        "./dev/mixer": ("crw-rw----", "0/29"),
        "./dev/mpu401data": ("crw-rw----", "0/29"),
        "./dev/mpu401stat": ("crw-rw----", "0/29"),
        "./dev/null": ("crw-rw-rw-", "0/0"),
        "./dev/port": ("crw-r-----", "0/15"),
        "./dev/ram0": ("brw-rw----", "0/6"),
        "./dev/ram10": ("brw-rw----", "0/6"),
        "./dev/ram11": ("brw-rw----", "0/6"),
        "./dev/ram12": ("brw-rw----", "0/6"),
        "./dev/ram13": ("brw-rw----", "0/6"),
        "./dev/ram14": ("brw-rw----", "0/6"),
        "./dev/ram15": ("brw-rw----", "0/6"),
        "./dev/ram16": ("brw-rw----", "0/6"),
        "./dev/ram1": ("brw-rw----", "0/6"),
        "./dev/ram2": ("brw-rw----", "0/6"),
        "./dev/ram3": ("brw-rw----", "0/6"),
        "./dev/ram4": ("brw-rw----", "0/6"),
        "./dev/ram5": ("brw-rw----", "0/6"),
        "./dev/ram6": ("brw-rw----", "0/6"),
        "./dev/ram7": ("brw-rw----", "0/6"),
        "./dev/ram8": ("brw-rw----", "0/6"),
        "./dev/ram9": ("brw-rw----", "0/6"),
        "./dev/random": ("crw-rw-rw-", "0/0"),
        "./dev/rmidi0": ("crw-rw----", "0/29"),
        "./dev/rmidi1": ("crw-rw----", "0/29"),
        "./dev/rmidi2": ("crw-rw----", "0/29"),
        "./dev/rmidi3": ("crw-rw----", "0/29"),
        "./dev/sequencer": ("crw-rw----", "0/29"),
        "./dev/smpte0": ("crw-rw----", "0/29"),
        "./dev/smpte1": ("crw-rw----", "0/29"),
        "./dev/smpte2": ("crw-rw----", "0/29"),
        "./dev/smpte3": ("crw-rw----", "0/29"),
        "./dev/sndstat": ("crw-rw----", "0/29"),
        "./dev/tty0": ("crw-------", "0/5"),
        "./dev/tty1": ("crw-------", "0/5"),
        "./dev/tty2": ("crw-------", "0/5"),
        "./dev/tty3": ("crw-------", "0/5"),
        "./dev/tty4": ("crw-------", "0/5"),
        "./dev/tty5": ("crw-------", "0/5"),
        "./dev/tty6": ("crw-------", "0/5"),
        "./dev/tty7": ("crw-------", "0/5"),
        "./dev/tty8": ("crw-------", "0/5"),
        "./dev/tty9": ("crw-------", "0/5"),
        "./dev/tty": ("crw-rw-rw-", "0/5"),
        "./dev/urandom": ("crw-rw-rw-", "0/0"),
        "./dev/zero": ("crw-rw-rw-", "0/0"),
    },
    "core18": {
        "./dev/null": ("crw-rw-rw-", "0/0"),
        "./dev/random": ("crw-rw-rw-", "0/0"),
        "./dev/urandom": ("crw-rw-rw-", "0/0"),
        "./dev/zero": ("crw-rw-rw-", "0/0"),
    },
    "core20": {
        "./dev/null": ("crw-rw-rw-", "0/0"),
        "./dev/random": ("crw-rw-rw-", "0/0"),
        "./dev/urandom": ("crw-rw-rw-", "0/0"),
        "./dev/zero": ("crw-rw-rw-", "0/0"),
    },
    "core22": {
        "./dev/null": ("crw-rw-rw-", "0/0"),
        "./dev/random": ("crw-rw-rw-", "0/0"),
        "./dev/urandom": ("crw-rw-rw-", "0/0"),
        "./dev/zero": ("crw-rw-rw-", "0/0"),
    },
    "test-snapd-core18": {  # grandfathered
        "./dev/null": ("crw-rw-rw-", "0/0"),
        "./dev/random": ("crw-rw-rw-", "0/0"),
        "./dev/urandom": ("crw-rw-rw-", "0/0"),
        "./dev/zero": ("crw-rw-rw-", "0/0"),
    },
    "ubuntu-core": {
        "./dev/adbmouse": ("crw-rw----", "0/0"),
        "./dev/agpgart": ("crw-rw----", "0/44"),
        "./dev/amigamouse1": ("crw-rw----", "0/0"),
        "./dev/amigamouse": ("crw-rw----", "0/0"),
        "./dev/apm_bios": ("crw-rw----", "0/0"),
        "./dev/atarimouse": ("crw-rw----", "0/0"),
        "./dev/atibm": ("crw-rw----", "0/0"),
        "./dev/audio1": ("crw-rw----", "0/29"),
        "./dev/audio2": ("crw-rw----", "0/29"),
        "./dev/audio3": ("crw-rw----", "0/29"),
        "./dev/audio": ("crw-rw----", "0/29"),
        "./dev/audioctl": ("crw-rw----", "0/29"),
        "./dev/beep": ("crw-rw----", "0/0"),
        "./dev/console": ("crw-------", "0/5"),
        "./dev/dsp1": ("crw-rw----", "0/29"),
        "./dev/dsp2": ("crw-rw----", "0/29"),
        "./dev/dsp3": ("crw-rw----", "0/29"),
        "./dev/dsp": ("crw-rw----", "0/29"),
        "./dev/exttrp": ("crw-rw----", "0/0"),
        "./dev/full": ("crw-rw-rw-", "0/0"),
        "./dev/hfmodem": ("crw-rw----", "0/0"),
        "./dev/hwtrap": ("crw-rw----", "0/0"),
        "./dev/inportbm": ("crw-rw----", "0/0"),
        "./dev/jbm": ("crw-rw----", "0/0"),
        "./dev/kmem": ("crw-r-----", "0/15"),
        "./dev/led": ("crw-rw----", "0/0"),
        "./dev/logibm": ("crw-rw----", "0/0"),
        "./dev/loop0": ("brw-rw----", "0/6"),
        "./dev/loop1": ("brw-rw----", "0/6"),
        "./dev/loop2": ("brw-rw----", "0/6"),
        "./dev/loop3": ("brw-rw----", "0/6"),
        "./dev/loop4": ("brw-rw----", "0/6"),
        "./dev/loop5": ("brw-rw----", "0/6"),
        "./dev/loop6": ("brw-rw----", "0/6"),
        "./dev/loop7": ("brw-rw----", "0/6"),
        "./dev/mem": ("crw-r-----", "0/15"),
        "./dev/mergemem": ("crw-rw----", "0/0"),
        "./dev/midi00": ("crw-rw----", "0/29"),
        "./dev/midi01": ("crw-rw----", "0/29"),
        "./dev/midi02": ("crw-rw----", "0/29"),
        "./dev/midi03": ("crw-rw----", "0/29"),
        "./dev/midi0": ("crw-rw----", "0/29"),
        "./dev/midi1": ("crw-rw----", "0/29"),
        "./dev/midi2": ("crw-rw----", "0/29"),
        "./dev/midi3": ("crw-rw----", "0/29"),
        "./dev/mixer1": ("crw-rw----", "0/29"),
        "./dev/mixer2": ("crw-rw----", "0/29"),
        "./dev/mixer3": ("crw-rw----", "0/29"),
        "./dev/mixer": ("crw-rw----", "0/29"),
        "./dev/modreq": ("crw-rw----", "0/0"),
        "./dev/mpu401data": ("crw-rw----", "0/29"),
        "./dev/mpu401stat": ("crw-rw----", "0/29"),
        "./dev/msr": ("crw-rw----", "0/0"),
        "./dev/null": ("crw-rw-rw-", "0/0"),
        "./dev/nvram": ("crw-rw----", "0/0"),
        "./dev/openprom": ("crw-rw-r--", "0/0"),
        "./dev/pc110pad": ("crw-rw----", "0/0"),
        "./dev/pciconf": ("crw-rw----", "0/0"),
        "./dev/pmu": ("crw-rw----", "0/0"),
        "./dev/port": ("crw-r-----", "0/15"),
        "./dev/psaux": ("crw-rw----", "0/0"),
        "./dev/ram0": ("brw-rw----", "0/6"),
        "./dev/ram10": ("brw-rw----", "0/6"),
        "./dev/ram11": ("brw-rw----", "0/6"),
        "./dev/ram12": ("brw-rw----", "0/6"),
        "./dev/ram13": ("brw-rw----", "0/6"),
        "./dev/ram14": ("brw-rw----", "0/6"),
        "./dev/ram15": ("brw-rw----", "0/6"),
        "./dev/ram16": ("brw-rw----", "0/6"),
        "./dev/ram1": ("brw-rw----", "0/6"),
        "./dev/ram2": ("brw-rw----", "0/6"),
        "./dev/ram3": ("brw-rw----", "0/6"),
        "./dev/ram4": ("brw-rw----", "0/6"),
        "./dev/ram5": ("brw-rw----", "0/6"),
        "./dev/ram6": ("brw-rw----", "0/6"),
        "./dev/ram7": ("brw-rw----", "0/6"),
        "./dev/ram8": ("brw-rw----", "0/6"),
        "./dev/ram9": ("brw-rw----", "0/6"),
        "./dev/random": ("crw-rw-rw-", "0/0"),
        "./dev/relay16": ("crw-rw----", "0/0"),
        "./dev/relay8": ("crw-rw----", "0/0"),
        "./dev/rmidi0": ("crw-rw----", "0/29"),
        "./dev/rmidi1": ("crw-rw----", "0/29"),
        "./dev/rmidi2": ("crw-rw----", "0/29"),
        "./dev/rmidi3": ("crw-rw----", "0/29"),
        "./dev/rtc": ("crw-rw----", "0/0"),
        "./dev/sequencer": ("crw-rw----", "0/29"),
        "./dev/smouse": ("crw-rw----", "0/0"),
        "./dev/smpte0": ("crw-rw----", "0/29"),
        "./dev/smpte1": ("crw-rw----", "0/29"),
        "./dev/smpte2": ("crw-rw----", "0/29"),
        "./dev/smpte3": ("crw-rw----", "0/29"),
        "./dev/sndstat": ("crw-rw----", "0/29"),
        "./dev/sunmouse": ("crw-rw----", "0/0"),
        "./dev/temperature": ("crw-rw----", "0/0"),
        "./dev/tty0": ("crw-------", "0/5"),
        "./dev/tty1": ("crw-------", "0/5"),
        "./dev/tty2": ("crw-------", "0/5"),
        "./dev/tty3": ("crw-------", "0/5"),
        "./dev/tty4": ("crw-------", "0/5"),
        "./dev/tty5": ("crw-------", "0/5"),
        "./dev/tty6": ("crw-------", "0/5"),
        "./dev/tty7": ("crw-------", "0/5"),
        "./dev/tty8": ("crw-------", "0/5"),
        "./dev/tty9": ("crw-------", "0/5"),
        "./dev/tty": ("crw-rw-rw-", "0/5"),
        "./dev/urandom": ("crw-rw-rw-", "0/0"),
        "./dev/watchdog": ("crw-rw----", "0/0"),
        "./dev/zero": ("crw-rw-rw-", "0/0"),
    },
}

# Snaps that may specify 'daemon' with 'browser-support'. Care must be taken
# since snaps running with 'daemon' run as root and this grants more privileges
# than intended. As of 2020-01-09 (see
# https://forum.snapcraft.io/t/problem-with-releasing-kiosk-app/14861/14):
#
# "Today, there are two options:
#  * if the snap is intended to be included in a brand store 1, then the
#    publisher can distribute the snap in their brand store without worrying
#    about the check (because the publisher owns the brand and access to the
#    brand store is limited to devices associated with the brand)
#  * if the snap is intended to be distributed via the public store, then:
#    * the snap should be reviewed for suitability for distribution in the
#      public store (eg, whether or not, due to branding, intended use, device
#      deployments, etc, the snap makes sense for the public store)
#    * the publisher should be vetted, as with classic snaps
#    * the publisher modifies the snap to use system-usernames where the
#      daemon is modified to drop privileges and the publisher agrees to not
#      revert to starting as root
sec_browser_support_overrides = [
    # grandfathered overrides
    "chromium-mir-kiosk",  # mir team
    "dashkiosk-client-browser",  # ogra
    "screencloudplayer",
    "webdemo",
    # new process overrides
    "beefee-terminal-app",  # https://forum.snapcraft.io/t/problem-with-releasing-kiosk-app/14861/28
    "ozone-display",  # https://forum.snapcraft.io/t/review-request-for-ozone-display/19548/4
    "krellian-kiosk",  # https://forum.snapcraft.io/t/request-for-daemon-browser-support-for-krellian-kiosk/18873/34
]

# Snaps that for some reason do not resquash properly. This is primarily used
# for partners that are stuck on an older snapcraft.
sec_resquashfs_overrides = [
    "clion",  # jetbrains
    "clion-nsg",
    "datagrip",
    "gogland",
    "goland",
    "intellij-idea-community",
    "intellij-idea-ultimate",
    "kotlin",
    "kotlin-native",
    "phpstorm",
    "pycharm-community",
    "pycharm-educational",
    "pycharm-professional",
    "rider",
    "rubymine",
    "webstorm",  # end jetbrains
]

#
# HISTORICAL
#
# Before snapd 2.44, snapd did not have proper controls on what the interface
# reference must be in the snap declaration, so we had a cheap test to ensure
# that the interface reference is in the list of allowed references. Older
# snaps with existing overrides will remain here, but new ones should use the
# 'plug-names' mechanism.
#
# https://forum.snapcraft.io/t/requesting-auto-connection-of-personal-files-to-sam-cli/10641/10
# https://wiki.canonical.com/AppStore/Reviews#Snap_declaration_assertion_versions
#
sec_iface_ref_overrides = {
    "personal-files": {
        "amass": ["dot-amass"],
        "aws-cli": ["dot-aws"],
        "aws-sam-cli": ["config-aws"],
        "autotrash-unofficial": ["dot-local-share-trash"],
        "charmcraft": ["dot-hgrc", "gitconfig"],
        "chromium": ["chromium-config"],
        "cloudscale-cli": ["dot-cloudscale-ini"],
        "cw-sh": ["dot-aws-config-credentials"],
        "doctl": ["doctl-config", "dot-docker", "kube-config"],
        "dotrun": ["dot-npmrc", "dot-yarnrc"],
        "dynocsv": ["aws-config-credentials"],
        "enonic": ["dot-enonic"],
        "exoscale-cli": ["dot-exoscale"],
        "fac": ["dot-fac-yaml", "gitconfig"],
        "fluxctl": ["kube-config"],
        "gallery-dl": ["config-gallery-dl"],
        "ghtt": ["gitconfig"],
        "git-machete": ["gitconfig"],
        "gitl": ["gitconfig"],
        "glances": ["home-glances-config"],
        "guvcview": ["config-guvcview2"],
        "hw-probe": ["dot-local-share-xorg-logs"],
        "icdiff": ["gitconfig"],
        "inkscape": ["dot-config-inkscape"],
        "jaas": ["dot-local-share-juju"],
        "juju-bmc": ["dot-local-share-juju", "dot-maascli-db"],
        "k9s": ["kube-config"],
        "kubefwd": ["config-kube"],
        "kubernetes-worker": ["dot-kube"],
        "kubicorn": ["kube-config"],
        "liquibase": ["dot-m2-repository"],
        "ludo": ["config-ludo"],
        "microk8s": ["dot-kube"],
        "ngrok": ["ngrok-config"],
        "openstackclients": ["dot-config-openstack-clouds-yaml"],
        "popeye": ["kube-config"],
        "rain": ["config-aws"],
        "redis-desktop-manager": ["dot-rdm"],
        "rofi-totp": ["dot-gauth"],
        "shfmt": ["dot-editorconfig"],
        "snap-store": ["dot-snap-auth-json"],
        "spread": ["dot-spread", "dot-config-gcloud"],
        "stimmtausch": ["dot-config-stimmtausch"],
        "stmg": ["dot-local-share-stmm-games"],
        "universal-ctags": ["dot-ctags"],
        "vht": ["dot-vault-token"],
        "wtf-tui": ["dot-config-wtf-config-yml"],
    },
    "system-files": {
        "charmcraft": ["etc-hgrc"],
        "cvescan": ["apt-dpkg-db", "hostfs-var-lib-ubuntu-advantage-status-json"],
        "gallery-dl": ["etc-gallery-dl"],
        "get-iplayer": ["etc-get-iplayer-options"],
        "glances": ["etc-glances-config"],
        "gnome-system-monitor": ["run-systemd-sessions"],
        "jabref": [
            "hostfs-mozilla-native-messaging-jabref",
            "etc-opt-chrome-native-messaging-jabref",
            "etc-chromium-native-messaging-jabref",
            "etc-opt-edge-native-messaging-jabref",
        ],
        "snap-store": ["hostfs-usr-share-applications"],
    },
}

sec_iface_ref_matches_base_decl_overrides = {
    "caracalla": [("content", "alsa")],
    "caracalla-iot-nxt": [("content", "alsa")],
    "joule": [("content", "alsa")],
}

# Snaps that have legitimate need for executable stack but otherwise work fine
# in strict mode
func_execstack_overrides = [
    "checkbox-balboa",
    "checkbox-oem-qa",
    "checkbox-plano",
    "checkbox-plano-classic",
    "checkbox-snappy",
    "checkbox-tampere",
    "checkbox-tillamook",
    "enemy-territory",
    "microsoft-edge",
    "microsoft-edge-beta",
    "microsoft-edge-dev",
    "store-checker",
]

# Some files from staged packages are known to have execstack, so don't flag
# snaps with these since they may have incidentally included them. IMPORTANT:
# some files in the archive have execstack but should have it stripped, so
# don't include those here.
func_execstack_skipped_pats = [
    "boot/.*",
    "lib/klibc.*",
    "usr/bin/.*-mingw.*-gnat.*",
    "usr/bin/gnat.*",
    "usr/bin/.*gnat.*-[0-9]$",
    "usr/bin/grub.*",
    "usr/lib/debug/.*",
    "usr/lib/grub/.*",
    "usr/lib/libatlas-test/.*",
    "usr/.*/libgnat.*",
    "usr/lib.*/.*nvidia.*",
    "usr/lib/syslinux/modules/.*",
    "usr/share/dpdk/test/.*",
    # investigate
    "usr/lib/arm-linux-gnueabihf/libx264.so.148",
    "usr/lib/arm-linux-gnueabihf/libvolk.so.1.1",
    # s390x firmware in lxd snap (lxd ships in share/, so allow it too)
    "share/qemu/s390-ccw.img",
    "share/qemu/s390-netboot.img",
    "usr/share/qemu/s390-ccw.img",
    "usr/share/qemu/s390-netboot.img",
]

# Most base snaps require certain mountpoints to be present. Snaps listed here
# won't be flagged for manual review.
func_base_mountpoints_overrides = ["bare"]

# Allow skipping checks for some files
func_base_state_files_overrides = {
    "core": [
        # skip snapd-specific files per mvo
        "usr/lib/snapd/.*",
        "var/cache/snapd/.*",
        "var/lib/snapd/.*",
    ]
}

# Allow skipping checks for some snaps
func_base_state_files_snaps_overrides = {"core22": "20220421"}

# By default we don't regulate which snaps specify which base snaps, but some
# base snaps are highly specialized, so we limit what can use them. Base snaps
# whose name is not a key in this dict don't flag for review. For base snaps
# whose name is a key in this dict, snaps not listed in the list for the base
# snap are flagged for manual review.
# https://forum.snapcraft.io/t/manual-review-of-base-snaps/2839/9
lint_redflagged_base_dep_override = {
    "solus-runtime-gaming": ["linux-steam-integration"]
}

# For a given snapd_<username>, list the snaps that are allowed to
# specify it. Note, as a special case, 'snap_daemon' may be used
# by any snap and is not tracked here.
lint_system_usernames_override = {"snap_microk8s": ["microk8s"]}

# Some publisher_emails represent a shared account. For snaps with a shared
# email, also send to other addresses.
canonical_anbox = ["stephane.graber@canonical.com", "simon.fels@canonical.com"]

canonical_charmcraft = [
    "facundo.batista@canonical.com",
    "sergio.schvezov@canonical.com",
]

canonical_commercial_systems = [
    "uros.jovanovic@canonical.com",
    "francesco.banconi@canonical.com",
    "casey.marshall@canonical.com",
    "martin.hilton@canonical.com",
]
canonical_desktop = [
    "ken.vandine@canonical.com",
    "sebastien.bacher@canonical.com",
]

canonical_edgex = [
    "tony.espy@canonical.com",
    "siggi.skulason@canonical.com",
    "haresh.kainth@canonical.com",
]

canonical_enablement = [
    "snap-update-verification@lists.canonical.com",
    "pascal.morin@canonical.com",
    "tony.espy@canonical.com",
    "loic.minier@canonical.com",
]

canonical_foundations = [
    "michael.hudson@canonical.com",
    "steve.langasek@canonical.com",
]

canonical_kernel = [
    "brad.figg@canonical.com",
    "terry.rudd@canonical.com",
    "dimitri.ledkov@canonical.com",
]

canonical_hwe = [
    "anthony.wong@canonical.com",
    "brad.figg@canonical.com",
    "shrirang.bagul@canonical.com",
]

canonical_juju = ["ian.booth@canonical.com", "john.meinel@canonical.com"]

canonical_k8s = ["chris.sanders@canonical.com", "tim.van.steenburgh@canonical.com"]

canonical_livepatch = ["benjamin.romer@canonical.com", "marcelo.cerri@canonical.com"]

canonical_lp = ["william.grant@canonical.com", "colin.watson@canonical.com"]

canonical_lxd = ["stephane.graber@canonical.com", "free.ekanayaka@canonical.com"]

canonical_maas = ["adam.collard@canonical.com", "blake.rouse@canonical.com"]

canonical_mir = [
    "alan.griffiths@canonical.com",
    "gerry.boland@canonical.com",
    "michal.sawicz@canonical.com",
]

canonical_multipass = canonical_mir

canonical_openstack = ["billy.olsen@canonical.com", "james.page@canonical.com"]

# TODO: Add Canonical rocks team
canonical_rocks = []

canonical_security = [
    "alex.murray@canonical.com",
    "emilia.torino@canonical.com",
]

canonical_server = ["rick.harding@canonical.com", "robie.basak@canonical.com"]

canonical_snapd = [
    "gustavo.niemeyer@canonical.com",
    "samuele.pedroni@canonical.com",
    "michael.vogt@canonical.com",
]

canonical_snapcraft = ["chris.patterson@canonical.com", "sergio.schvezov@canonical.com"]

# snaps@canonical.com used to be 'snappy-canonical-storeaccount@canonical.com'
# but it was changed a little while ago
update_publisher_overrides = {
    "snaps@canonical.com": {
        "alsa-utils": canonical_enablement,
        "avahi": canonical_enablement,
        "aws-kernel": canonical_kernel,
        "azure-kernel": canonical_kernel,
        "bare": canonical_snapd,
        "base-18": canonical_snapd,
        "bcc": ["colin.king@canonical.com"] + canonical_kernel,
        "bluez": canonical_enablement,
        "candid": canonical_commercial_systems,
        "canonical-livepatch": canonical_livepatch,
        "caracalla-kernel": canonical_hwe,
        "cascade-kernel": canonical_hwe,
        "charmcraft": canonical_charmcraft,
        "charm": canonical_juju,
        "chromium": ["olivier.tilloy@canonical.com"] + canonical_desktop,
        "chromium-ffmpeg": ["olivier.tilloy@canonical.com"] + canonical_desktop,
        "chromium-mir-kiosk": ["olivier.tilloy@canonical.com"] + canonical_mir,
        "classic": canonical_snapd,
        "cm3": canonical_snapd,
        "conjure-up": canonical_k8s,
        "core": canonical_snapd,
        "core16": canonical_snapd,
        "core18": canonical_snapd,
        "core20": canonical_snapd,
        "core22": canonical_snapd,
        "cvescan": canonical_security,
        "degw001-kernel": canonical_kernel,
        "dell-edge-iot-kernel": canonical_kernel,
        "docker": canonical_enablement,
        "dragonboard": canonical_snapd,
        "dragonboard-kernel": canonical_kernel,
        "easy-openvpn": canonical_enablement,
        "edgex-app-service-configurable": canonical_edgex,
        "edgex-cli": canonical_edgex,
        "edgex-device-camera": canonical_edgex,
        "edgex-device-grove": canonical_edgex,
        "edgex-device-modbus": canonical_edgex,
        "edgex-device-mqtt": canonical_edgex,
        "edgex-device-rest": canonical_edgex,
        "edgex-device-snmp": canonical_edgex,
        "edgex-ui": canonical_edgex,
        "edgex-ui-go": canonical_edgex,
        "edgexfoundry": canonical_edgex,
        "eog": canonical_desktop,
        "etcd": canonical_k8s,
        "gcp-kernel": canonical_kernel,
        "gedit": canonical_desktop,
        "git-ubuntu": canonical_server,
        "gke-kernel": canonical_kernel,
        "gnome-3-26-1604": canonical_desktop,
        "gnome-3-28-1804": canonical_desktop,
        "gnome-3-32-1804": canonical_desktop,
        "gnome-3-32-1804-sdk": canonical_desktop,
        "gnome-3-34-1804": canonical_desktop,
        "gnome-3-34-1804-sdk": canonical_desktop,
        "gnome-3-38-2004": canonical_desktop,
        "gnome-3-38-2004-sdk": canonical_desktop,
        "gnome-calculator": canonical_desktop,
        "gnome-calendar": canonical_desktop,
        "gnome-characters": canonical_desktop,
        "gnome-clocks": canonical_desktop,
        "gnome-contacts": canonical_desktop,
        "gnome-dictionary": canonical_desktop,
        "gnome-logs": canonical_desktop,
        "gnome-sudoku": canonical_desktop,
        "gnome-system-monitor": canonical_desktop,
        "godd": canonical_snapd,
        "governor-broker": canonical_k8s,
        "gtk-common-themes": canonical_desktop,
        "gtk2-common-themes": canonical_desktop,
        "hello": canonical_snapcraft,
        "intel-kernel": canonical_kernel,
        "intel-iotg-kernel": canonical_kernel,
        "iot-kernel": canonical_kernel,
        "joule-expansion": canonical_k8s,
        "juju": canonical_juju,
        "jq": canonical_snapd,
        "jq-core18": canonical_snapd,
        "kube-apiserver": canonical_k8s,
        "kube-controller-manager": canonical_k8s,
        "kube-proxy": canonical_k8s,
        "kube-scheduler": canonical_k8s,
        "kubeadm": canonical_k8s,
        "kubectl": canonical_k8s,
        "kubelet": canonical_k8s,
        "kubernetes-test": canonical_k8s,
        "kubernetes-worker": canonical_k8s,
        "libreoffice": canonical_desktop + ["marcus.tomlinson@canonical.com"],
        "locationd": canonical_enablement,
        "lp-build-snap": canonical_lp,
        "lxd": canonical_lxd,
        "maas": canonical_maas,
        "maas-cli": canonical_maas,
        "maas-test-db": canonical_maas,
        "mesa-core20": canonical_mir,
        "microk8s": canonical_k8s,
        "microk8s-integrator-macos": canonical_k8s,
        "microk8s-integrator-windows": canonical_k8s,
        "microstack": canonical_openstack,
        "mir-kiosk": canonical_mir,
        "mir-kiosk-apps": canonical_mir,
        "modem-manager": canonical_enablement,
        "multipass": canonical_multipass,
        "multipass-sshfs": canonical_multipass,
        "mysql-shell": canonical_openstack,
        "network-manager": canonical_enablement,
        "openstack": canonical_openstack,
        "openstackclients": canonical_openstack,
        "openwrt": canonical_enablement,
        "pc": canonical_snapd,
        "pc-kernel": canonical_kernel,
        "pc-lowlatency-kernel": canonical_kernel,
        "pi": canonical_snapd,
        "pi-kernel": canonical_kernel,
        "pi2": canonical_snapd,
        "pi2-kernel": canonical_kernel,
        "pi3": canonical_snapd,
        "prometheus": canonical_server,
        "pulseaudio": canonical_enablement,
        "quadrapassel": canonical_desktop,
        "review-tools": canonical_security,
        "se-test-tools": canonical_enablement,
        "simple-scan": canonical_desktop,
        "simplestreams": canonical_openstack,
        "smt": canonical_security,
        "snap-store": canonical_desktop,
        "snapcraft": canonical_snapcraft,
        "snapd": canonical_snapd,
        "snappy-debug": canonical_security,
        "snapweb": canonical_enablement,
        "nats": canonical_anbox,
        "stlouis-kernel": canonical_hwe,
        "strace-static": canonical_snapd,
        "subiquity": canonical_foundations,
        "test-snapd-accounts-service": canonical_snapd,
        "test-snapd-autopilot-consumer": canonical_snapd,
        "test-snapd-busybox-static": canonical_snapd,
        "test-snapd-cups-control-consumer": canonical_snapd,
        "test-snapd-dbus-consumer": canonical_snapd,
        "test-snapd-dbus-provider": canonical_snapd,
        "test-snapd-dbus-service": canonical_snapd,
        "test-snapd-eds": canonical_snapd,
        "test-snapd-fuse-consumer": canonical_snapd,
        "test-snapd-go-webserver": canonical_snapd,
        "test-snapd-gpio-memory-control": canonical_snapd,
        "test-snapd-gsettings": canonical_snapd,
        "test-snapd-hello-classic": canonical_snapd,
        "test-snapd-kernel-module-consumer": canonical_snapd,
        "test-snapd-location-control-provider": canonical_snapd,
        "test-snapd-network-status-provider": canonical_snapd,
        "test-snapd-openvswitch-support": canonical_snapd,
        "test-snapd-password-manager-consumer": canonical_snapd,
        "test-snapd-pc": canonical_snapd,
        "test-snapd-pc-kernel": canonical_snapd,
        "test-snapd-physical-memory-control": canonical_snapd,
        "test-snapd-python-webserver": canonical_snapd,
        "test-snapd-rsync-core18": canonical_snapd,
        "test-snapd-system-observe-consumer": canonical_snapd,
        "test-snapd-uhid": canonical_snapd,
        "test-snapd-upower-observe-consumer": canonical_snapd,
        "thunderbird": canonical_desktop,
        "tpm": canonical_enablement,
        "tpm2": canonical_enablement,
        "ubuntu-desktop-installer": canonical_desktop,
        "ubuntu-frame": canonical_mir,
        "ubuntu-frame-osk": canonical_mir,
        "ubuntu-image": canonical_foundations,
        "udisks2": canonical_enablement,
        "uefi-fw-tools": canonical_enablement,
        "ufw": canonical_security,
        "vault": canonical_openstack,
        "wifi-ap": canonical_enablement,
        "wifi-connect": canonical_enablement,
        "wpa-supplicant": canonical_enablement,
    },
    "rocks@canonical.com": {
        "redis": canonical_rocks,
        "nginx": canonical_rocks,
        "apache2": canonical_rocks,
        "memcached": canonical_rocks,
        "mysql": canonical_rocks,
        "postgres": canonical_rocks,
        "grafana": canonical_rocks,
        "cortex": canonical_rocks,
        "prometheus": canonical_rocks,
        "telegraf": canonical_rocks,
        "prometheus-alertmanager": canonical_rocks,
    },
}

# For Canonical supported snaps, add to what is staged (eg, to support git,
# snaps that don't build from debs, etc). The os and base snaps are currently
# treated separately and aren't listed here. Format:
#
#   update_stage_packages = {'<snap>[/<base>]': {'<deb>': '<version>|auto*'}}
#
# where <snap> is the snap to operate on, <deb> is the Ubuntu binary and
# <version> is the <deb> version. The special case of 'auto*' will use the
# 'version' field from the snap version in some capacity.
#
# '/<base>' may optionally be specified. When it is specified, a snap that
# specifies 'name: <snap>' and 'base: <base>' will be compared against this
# version instead. For example, with:
#   update_stage_packages = {
#       "foo": {"bar": "1.2"},
#       "foo/core18": {"bar": "2.0"},
#   }
# a snap named 'foo' whose revision uses 'base: core18' will have the deb 'bar'
# compared against version '2.0'. If a different revision specified a different
# base (or none at all), then 'bar' will be compared against '1.2'. In this
# manner, different tracks can target different bases and be compared against
# different revisions.
update_stage_packages = {
    "aws-kernel": {"linux-image-aws": "auto-kernel"},
    "azure-kernel": {"linux-image-azure": "auto-kernel"},
    "caracalla-kernel": {"linux-image-generic": "auto-kernel"},
    "cascade-kernel": {"linux-image-generic": "auto-kernel"},
    "dragonboard-kernel": {"linux-image-snapdragon": "auto-kernel"},
    "gcp-kernel": {"linux-image-gcp": "auto-kernel"},
    "gke-kernel": {"linux-image-gke": "auto-kernel"},
    "linux-generic-bbb": {"linux-image-generic": "auto-kernel"},
    # 'network-manager': {'network-manager': 'auto'},  # eventually
    "pc-kernel": {"linux-image-generic": "auto-kernel"},
    "pc-lowlatency-kernel": {"linux-image-generic": "auto-kernel"},
    "pi-kernel": {"linux-image-raspi2": "auto-kernel"},
    "pi2-kernel": {"linux-image-raspi2": "auto-kernel"},  # same as pi-kernel
    # Canonical Stack Snaps - changes should be approved by awe
    # - alsa-utils snapcraft.yaml doesn't specify base; mock xenial version
    "alsa-utils": {"alsa-utils": "1.1.0-0ubuntu5"},
    # - bluez snapcraft.yaml doesn't specify base; mock xenial version
    "bluez": {"bluez": "5.37-0ubuntu5.3"},
    # - locationd snapcraft.yaml doesn't specify base; mock xenial version
    "locationd": {"location-service": "3.0.0+16.04.20160405-0ubuntu1"},
    # - modem-manager snapcraft.yaml doesn't specify base; mock xenial version
    "modem-manager": {"modemmanager": "1.6.4-1ubuntu0.16.04.1"},
    # - network-manager snapcraft.yaml doesn't specify base; mock xenial
    "network-manager": {"network-manager": "1.2.6-0ubuntu0.16.04.3"},
    "network-manager/core18": {"network-manager": "1.10.6-2ubuntu1.1"},
    # - stlouis-kernel maintained by hwe
    "stlouis-kernel": {"linux-image-generic": "auto-kernel"},
    # - udisks2 snapcraft.yaml doesn't specify base; mock xenial versions
    "udisks2": {"udisks2": "2.1.7-1ubuntu1"},
    # - wifi-ap snapcraft.yaml doesn't specify base; mock xenial versions
    "wifi-ap": {"dnsmasq": "2.75-1", "wpa": "2.4-0ubuntu6"},
    # - wpa-supplicant snapcraft.yaml doesn't specify base; mock xenial
    "wpa-supplicant": {"wpa": "2.4-0ubuntu6"},
}

# For all/certain snaps, add to build-parts. This is a special case and we are
# only considering snapcraft as a build-part for every snap. Since manifest is
# present it means the snap was built using snapcraft.
# Format:
#   update_build_packages = {'<snap>': {'<deb>': '<version>|auto'}
#
# where <snap> is currently ignored, <deb> is the Ubuntu binary and <version>
# is the deb version. The special case of 'auto' will use the
# 'snapcraft-version' field from the snap. For now, only 'snapcraft' is
# supported for the '<deb>' and 'auto' for the version.
# TODO: update when fully support build-packages
update_build_packages = {"faked-by-review-tools": {"snapcraft": "auto"}}

# For certain packages, ignore USN secnotversion and use this override version
# instead. This allows sending USN notification for snap updates since
# snap's versions are not present in secnots.
# Format:
#   update_package_version = {'<pkg>': {'<part-key>': '<version>'}
#
# where <pkg> is the pkg to operate on during version comparison,
# <part-key> is the key in the manifest part where to look for the presence of
# <pkg> (i.e. only use this override if pkg in part-key for some part) and
# <version> is the version to use instead of secnotversion.
# TODO: update when fully support installed-snaps or further snapcraft updates
update_package_version = {"snapcraft": {"installed-snaps": "4.4.4"}}

# Some binary packages aren't worth alerting on since they don't contain
# affected binaries (eg, a package with only header files)
update_binaries_ignore = ["linux-headers-generic", "linux-libc-dev"]

# Some snaps may have legitimate access for external symlinks. This only says
# that some symlink may point to this target. It does not verify the name of
# the symlink (only the target).
common_external_symlink_override = {
    "chromium": ["usr/bin/xdg-open"],
    "microsoft-edge": ["usr/bin/xdg-open"],
    "microsoft-edge-beta": ["usr/bin/xdg-open"],
    "microsoft-edge-dev": ["usr/bin/xdg-open"],
    "skype": ["usr/bin/xdg-open"],
    "snapd": ["usr/lib/snapd/snap-device-helper"],
}
