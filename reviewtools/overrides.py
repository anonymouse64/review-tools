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
        "joule-drone-kernel",
        "joule-linux",
        "joule-linux-lool",
        "linux-generic-allwinner",
        "mako-kernel",
        "marvell-armada3700-kernel",
        "nitrogen6x-kernel",
        "nxp-ls1043a-kernel",
        "odroidxu4-kernel",
        "pc-lowlatency-kernel",
        "pi2-kernel-rt",
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
        "test-snapd-base",
        "test-snapd-core18",
        "fedora29",  # Community base snaps
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
classic_interfaces_exception = ["certbot", "juju", "microk8s"]

# List additional attributes that a particular snap may specify with a
# particular side of a particular interface (eg, for workaround content
# interface methodology)
interfaces_attribs_addons = {"microk8s": {"content": {"name/slots": ""}}}

#
# sr_security.py overrides
#
# Files with unusual modes that we'll allow for certain snaps.
# NOTE: when SNAP_FAKEROOT_RESQUASHFS=0 adding setuid/setgid files here
# will disable resquash enforcement.
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

# Snaps that may specify 'daemon' with 'browser-support'. Normally this
# shouldn't be granted because snaps running with 'daemon' run as root and this
# grants more privileges than intended.
sec_browser_support_overrides = [
    "chromium-mir-kiosk",  # mir team
    "dashkiosk-client-browser",  # ogra
    "screencloudplayer",
    "webdemo",
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

# https://forum.snapcraft.io/t/requesting-auto-connection-of-personal-files-to-sam-cli/10641/10
# Until snapd has better controls on what the interface reference must be in
# the snap declaration, we will have a cheap test to ensure that the interface
# reference is in the list of allowed references. We don't want to encode the
# snap declaration here too, which means a snap can use any of these with the
# passing snap declaration constraint.
#
# XXX: eventually, this will go away. snapd 2.44 adds plug-names/slot-names
# that should be used instead for personal-files, system-files, etc. We don't
# want to do this just yet though. See:
# https://wiki.canonical.com/AppStore/Reviews#Snap_declaration_assertion_versions
sec_iface_ref_overrides = {
    "personal-files": {
        "amass": ["dot-amass"],
        "aws-cli": ["dot-aws"],
        "aws-sam-cli": ["config-aws"],
        "chromium": ["chromium-config"],
        "cw-sh": ["dot-aws-config-credentials"],
        "doctl": ["doctl-config", "kube-config"],
        "dynocsv": ["aws-config-credentials"],
        "enonic": ["dot-enonic"],
        "exoscale-cli": ["dot-exoscale"],
        "fluxctl": ["kube-config"],
        "gallery-dl": ["config-gallery-dl"],
        "git-machete": ["gitconfig"],
        "gitl": ["gitconfig"],
        "glances": ["home-glances-config"],
        "guvcview": ["config-guvcview2"],
        "hw-probe": ["dot-local-share-xorg-logs"],
        "icdiff": ["gitconfig"],
        "jaas": ["dot-local-share-juju"],
        "k9s": ["kube-config"],
        "kubefwd": ["config-kube"],
        "kubernetes-worker": ["dot-kube"],
        "kubicorn": ["kube-config"],
        "liquibase": ["dot-m2-repository"],
        "ludo": ["config-ludo"],
        "microk8s": ["dot-kube"],
        "ngrok": ["ngrok-config"],
        "popeye": ["kube-config"],
        "rain": ["config-aws"],
        "redis-desktop-manager": ["dot-rdm"],
        "rofi-totp": ["dot-gauth"],
        "snap-store": ["dot-snap-auth-json"],
        "spread": ["dot-spread", "dot-config-gcloud"],
        "universal-ctags": ["dot-ctags"],
        "vht": ["dot-vault-token"],
    },
    "system-files": {
        "cvescan": ["apt-dpkg-db"],
        "gallery-dl": ["etc-gallery-dl"],
        "get-iplayer": ["etc-get-iplayer-options"],
        "glances": ["etc-glances-config"],
        "gnome-system-monitor": ["run-systemd-sessions"],
        "jabref": [
            "hostfs-mozilla-native-messaging-jabref",
            "etc-opt-chrome-native-messaging-jabref",
            "etc-chromium-native-messaging-jabref",
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
    "store-checker",
    "enemy-territory",
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
]

# Most base snaps require certain mountpoints to be present. Snaps listed here
# won't be flagged for manual review.
func_base_mountpoints_overrides = ["bare"]

# By default we don't regulate which snaps specify which base snaps, but some
# base snaps are highly specialized, so we limit what can use them. Base snaps
# whose name is not a key in this dict don't flag for review. For base snaps
# whose name is a key in this dict, snaps not listed in the list for the base
# snap are flagged for manual review.
# https://forum.snapcraft.io/t/manual-review-of-base-snaps/2839/9
lint_redflagged_base_dep_override = {
    "solus-runtime-gaming": ["linux-steam-integration"]
}

# Some publisher_emails represent a shared account. For snaps with a shared
# email, also send to other addresses.
canonical_commercial_systems = [
    "uros.jovanovic@canonical.com",
    "francesco.banconi@canonical.com",
    "casey.marshall@canonical.com",
    "martin.hilton@canonical.com",
]
canonical_desktop = [
    "ken.vandine@canonical.com",
    "sebastien.bacher@canonical.com",
    "will.cooke@canonical.com",
]

canonical_enablement = [
    "snap-update-verification@lists.canonical.com",
    "pascal.morin@canonical.com",
    "tony.espy@canonical.com",
    "loic.minier@canonical.com",
]

canonical_foundations = [
    "dimitri.ledkov@canonical.com",
    "michael.hudson@canonical.com",
    "patricia.gaughen@canonical.com",
    "steve.langasek@canonical.com",
]

canonical_kernel = ["brad.figg@canonical.com", "terry.rudd@canonical.com"]

canonical_hwe = [
    "anthony.wong@canonical.com",
    "brad.figg@canonical.com",
    "shrirang.bagul@canonical.com",
]

canonical_juju = ["ian.booth@canonical.com", "tim.penhey@canonical.com"]

canonical_k8s = ["adam.stokes@canonical.com", "tim.van.steenburgh@canonical.com"]

canonical_lp = ["william.grant@canonical.com", "colin.watson@canonical.com"]

canonical_lxd = ["stephane.graber@canonical.com", "free.ekanayaka@canonical.com"]

canonical_maas = ["adam.collard@canonical.com", "blake.rouse@canonical.com"]

canonical_mir = [
    "alan.griffiths@canonical.com",
    "gerry.boland@canonical.com",
    "michal.sawicz@canonical.com",
]

canonical_multipass = canonical_mir

canonical_openstack = ["ryan.beisner@canonical.com", "james.page@canonical.com"]

canonical_security = [
    "joe.mcmanus@canonical.com",
    "alex.murray@canonical.com",
    "jamie@canonical.com",
]

canonical_server = ["josh.powers@canonical.com", "robie.basak@canonical.com"]

canonical_snapd = [
    "gustavo.niemeyer@canonical.com",
    "samuele.pedroni@canonical.com",
    "michael.vogt@canonical.com",
]

canonical_snapcraft = ["martin.wimpress@canonical.com", "sergio.schvezov@canonical.com"]

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
        "caracalla-kernel": canonical_hwe,
        "cascade-kernel": canonical_hwe,
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
        "dell-edge-iot-kernel": canonical_kernel,
        "docker": canonical_enablement,
        "dragonboard": canonical_snapd,
        "dragonboard-kernel": canonical_kernel,
        "easy-openvpn": canonical_enablement,
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
        "gtk-common-themes": canonical_desktop,
        "gtk2-common-themes": canonical_desktop,
        "hello": canonical_snapcraft,
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
        "microk8s": canonical_k8s,
        "microstack": canonical_openstack,
        "mir-kiosk": canonical_mir,
        "mir-kiosk-apps": canonical_mir,
        "modem-manager": canonical_enablement,
        "multipass": canonical_multipass,
        "multipass-sshfs": canonical_multipass,
        "network-manager": canonical_enablement,
        "openstack": canonical_openstack,
        "openwrt": canonical_enablement,
        "pc": canonical_snapd,
        "pc-kernel": canonical_kernel,
        "pc-lowlatency-kernel": canonical_kernel,
        "pi": canonical_snapd,
        "pi-kernel": canonical_kernel,
        "pi2": canonical_snapd,
        "pi2-kernel": canonical_kernel,
        "pi3": canonical_snapd,
        "pulseaudio": canonical_enablement,
        "quadrapassel": canonical_desktop,
        "se-test-tools": canonical_enablement,
        "simple-scan": canonical_desktop,
        "smt": canonical_security,
        "snap-store": canonical_desktop,
        "snapcraft": canonical_snapcraft,
        "snapd": canonical_snapd,
        "snappy-debug": canonical_security,
        "snapweb": canonical_enablement,
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
        "tpm": canonical_enablement,
        "tpm2": canonical_enablement,
        "ubuntu-image": canonical_foundations,
        "udisks2": canonical_enablement,
        "uefi-fw-tools": canonical_enablement,
        "ufw": canonical_security,
        "wifi-ap": canonical_enablement,
        "wifi-connect": canonical_enablement,
        "wpa-supplicant": canonical_enablement,
    }
}

# For Canonical supported snaps, add to what is staged (eg, to support git,
# snaps that don't build from debs, etc). The os and base snaps are currently
# treated separately and aren't listed here. Format:
#
#   update_stage_packages = { '<snap>': { '<deb>': '<version>|auto*' }}
#
# where <snap> is the snap to operate on, <deb> is the Ubuntu binary and
# <version> is the <deb> version. The special case of 'auto*' will use the
# 'version' field from the snap version in some capacity
update_stage_packages = {
    "aws-kernel": {"linux-image-aws": "auto-kernel"},
    "azure-kernel": {"linux-image-azure": "auto-kernel"},
    "caracalla-kernel": {"linux-image-generic": "auto-kernel"},
    "cascade-kernel": {"linux-image-generic": "auto-kernel"},
    "dragonboard-kernel": {"linux-image-snapdragon": "auto-kernel"},
    "gcp-kernel": {"linux-image-gcp": "auto-kernel"},
    "gke-kernel": {"linux-image-gke": "auto-kernel"},
    "linux-generic-bbb": {"linux-image-generic": "auto-kernelabi"},
    # 'network-manager': {'network-manager': 'auto'},  # eventually
    "pc-kernel": {"linux-image-generic": "auto-kernel"},
    "pc-lowlatency-kernel": {"linux-image-generic": "auto-kernel"},
    "pi-kernel": {"linux-image-raspi2": "auto-kernel"},
    "pi2-kernel": {"linux-image-raspi2": "auto-kernel"},  # same as pi-kernel
    # Canonical Stack Snaps - changes should be approved by awe
    # - alsa-utils snapcraft.yaml doesn't specify base; mock xenial version
    "alsa-utils": {"alsa-utils": "1.1.0-0ubuntu5"},
    # - bluez snapcraft.yaml doesn't specify base; mock xenial version
    "bluez": {"bluez": "5.37-0ubuntu5.1"},
    # - locationd snapcraft.yaml doesn't specify base; mock xenial version
    "locationd": {"location-service": "3.0.0+16.04.20160405-0ubuntu1"},
    # - modem-manager snapcraft.yaml doesn't specify base; mock xenial version
    "modem-manager": {"modemmanager": "1.6.4-1ubuntu0.16.04.1"},
    # - network-manager snapcraft.yaml doesn't specify base; mock xenial
    "network-manager": {"network-manager": "1.2.6-0ubuntu0.16.04.3"},
    # - stlouis-kernel maintained by hwe
    "stlouis-kernel": {"linux-image-generic": "auto-kernel"},
    # - udisks2 snapcraft.yaml doesn't specify base; mock xenial versions
    "udisks2": {"udisks2": "2.1.7-1ubuntu1"},
    # - wifi-ap snapcraft.yaml doesn't specify base; mock xenial versions
    "wifi-ap": {"dnsmasq": "2.75-1", "wpa": "2.4-0ubuntu6"},
    # - wpa-supplicant snapcraft.yaml doesn't specify base; mock xenial
    "wpa-supplicant": {"wpa": "2.4-0ubuntu6"},
}


# Some binary packages aren't worth alerting on since they don't contain
# affected binaries (eg, a package with only header files)
update_binaries_ignore = ["linux-headers-generic", "linux-libc-dev"]

# Some snaps may have legitimate access for external symlinks. This only says
# that some symlink may point to this target. It does not verify the name of
# the symlink (only the target).
common_external_symlink_override = {
    "chromium": ["usr/bin/xdg-open"],
    "snapd": ["usr/lib/snapd/snap-device-helper"],
}
