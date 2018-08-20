'''overrides.py: overrides for various functions'''
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
# sr_declaration.py overrides
#
# List of attributes that always successfully match (ie, so we don't
# flag on them).
iface_attributes_noflag = ['$SLOT(content)']

#
# sr_lint.py overrides
#
# To be removed. For now we know that snap names have a 1 to 1 mapping
# to publishers so we can whitelist snap names for snap types to not
# flag for manual review.
# NOTE: this will eventually move to assertions
redflagged_snap_types_overrides = {
    'kernel': ['dragonboard-kernel',  # Canonical reference kernels
               'linux-generic-bbb',
               'pc-kernel',
               'pi2-kernel',
               'aws-kernel',  # @canonical.com kernels
               'azure-kernel',
               'freescale-ls1043a-kernel',
               'gcp-kernel',
               'gke-kernel',
               'hummingboard-kernel',
               'joule-drone-kernel',
               'joule-linux',
               'joule-linux-lool',
               'linux-generic-allwinner',
               'mako-kernel',
               'marvell-armada3700-kernel',
               'nxp-ls1043a-kernel',
               'odroidxu4-kernel',
               'pi2-kernel-rt',
               'roseapple-pi-kernel',
               'roseapple-pi-kernel-ondra',
               'artik5-linux',  # 3rd party vendor kernels
               'artik10-linux',
               'bubblegum96-kernel',
               'eragon410-kernel',
               'linux-generic-bbb',
               'rexroth-xm21-kernel',
               'nitrogen-kernel',
               'teal-kernel',
               'telig-kernel',
               'tsimx6-kernel',
               ],
    'os': ['core',
           'ubuntu-core'
           ],
    'gadget': ['cm3',        # Canonical reference gadgets
               'dragonboard',
               'pc',
               'pi2',
               'pi3',
               'cm3-ondra',  # @canonical.com gadgets
               'cm3-openhab',
               'hikey-snappy-gadget',
               'hummingboard',
               'joule',
               'nanopi-air',
               'nanopi-neo',
               'nxp-ls1043ardb-gadget',
               'odroid-xu4',
               'orangepi-zero',
               'pi3-ondra',
               'pi3-openhab',
               'pi3-unipi',
               'pi2kyle',
               'pi3testbootsplash',
               'roseapple-pi',
               'sabrelite',
               'wdl-nextcloud',
               'wdl-nextcloud-pi2',
               'artik5',  # 3rd party vendor gadgets
               'artik10',
               'bubblegum96-gadget',
               'dragonboard-turtlebot-kyrofa',
               'eragon410',
               'eragon-sunny',
               'lemaker-guitar-gadget',
               'nitrogen-gadget',
               'pc-turtlebot-kyrofa',
               'rexroth-xm21',
               'subutai-pc',
               'telig',
               'tsimx6-gadget',
               ],
    'base': ['bare',                  # Canonical base snaps
             'base-18',
             'core16',
             'core18',
             'test-snapd-base',
             'solus-runtime-gaming',  # Community base snaps
             ],
}

# List of snaps that may specify an interface that requires a desktop file but
# not supply a desktop file itself.
desktop_file_exception = ['emoj',
                          'ffscreencast',
                          'pulsemixer',
                          ]

#
# sr_security.py overrides
#
# Files with unusual modes that we'll allow for certain snaps.
# NOTE: when SNAP_FAKEROOT_RESQUASHFS=0 adding setuid/setgid files here
# will disable resquash enforcement.
sec_mode_overrides = {
    'bare': {},
    'base-18': {
        './bin/mount': 'rwsr-xr-x',
        './bin/su': 'rwsr-xr-x',
        './bin/umount': 'rwsr-xr-x',
        './sbin/pam_extrausers_chkpwd': 'rwxr-sr-x',
        './sbin/unix_chkpwd': 'rwxr-sr-x',
        './tmp': 'rwxrwxrwt',
        './usr/bin/chage': 'rwxr-sr-x',
        './usr/bin/chfn': 'rwsr-xr-x',
        './usr/bin/chsh': 'rwsr-xr-x',
        './usr/bin/expiry': 'rwxr-sr-x',
        './usr/bin/gpasswd': 'rwsr-xr-x',
        './usr/bin/newgrp': 'rwsr-xr-x',
        './usr/bin/passwd': 'rwsr-xr-x',
        './usr/bin/ssh-agent': 'rwxr-sr-x',
        './usr/bin/sudo': 'rwsr-xr-x',
        './usr/bin/wall': 'rwxr-sr-x',
        './usr/lib/dbus-1.0/dbus-daemon-launch-helper': 'rwsr-xr--',
        './usr/lib/openssh/ssh-keysign': 'rwsr-xr-x',
        './var/local': 'rwxrwsr-x',
        './var/mail': 'rwxrwsr-x',
        './var/tmp': 'rwxrwxrwt',
    },
    'chrome-test': {  # chrome-test from Canonical
        './opt/google/chrome/chrome-sandbox': 'rwsr-xr-x',
    },
    'chromium': {  # chromium from Canonical
        './usr/lib/chromium-browser/chrome-sandbox': 'r-sr-xr-x',
    },
    'chromium-mir-kiosk': {  # chromium from Canonical with XWayland, etc
        './usr/lib/chromium-browser/chrome-sandbox': 'r-sr-xr-x',
    },
    'core': {
        './bin/mount': 'rwsr-xr-x',
        './bin/ping': 'rwsr-xr-x',
        './bin/ping6': 'rwsr-xr-x',
        './bin/su': 'rwsr-xr-x',
        './bin/umount': 'rwsr-xr-x',
        './etc/chatscripts': 'rwxr-s---',
        './etc/ppp/peers': 'rwxr-s---',
        './run/lock': 'rwxrwxrwt',
        './sbin/pam_extrausers_chkpwd': 'rwxr-sr-x',
        './sbin/unix_chkpwd': 'rwxr-sr-x',
        './tmp': 'rwxrwxrwt',
        './usr/bin/chage': 'rwxr-sr-x',
        './usr/bin/chfn': 'rwsr-xr-x',
        './usr/bin/chsh': 'rwsr-xr-x',
        './usr/bin/crontab': 'rwxr-sr-x',
        './usr/bin/dotlockfile': 'rwxr-sr-x',
        './usr/bin/expiry': 'rwxr-sr-x',
        './usr/bin/gpasswd': 'rwsr-xr-x',
        './usr/bin/mail-lock': 'rwxr-sr-x',
        './usr/bin/mail-unlock': 'rwxr-sr-x',
        './usr/bin/mail-touchlock': 'rwxr-sr-x',
        './usr/bin/newgrp': 'rwsr-xr-x',
        './usr/bin/passwd': 'rwsr-xr-x',
        './usr/bin/ssh-agent': 'rwxr-sr-x',
        './usr/bin/sudo': 'rwsr-xr-x',
        './usr/bin/wall': 'rwxr-sr-x',
        './usr/lib/dbus-1.0/dbus-daemon-launch-helper': 'rwsr-xr--',
        './usr/lib/openssh/ssh-keysign': 'rwsr-xr-x',
        './usr/lib/snapd/snap-confine': 'rwsr-sr-x',
        './usr/local/lib/python3.5': 'rwxrwsr-x',
        './usr/local/lib/python3.5/dist-packages': 'rwxrwsr-x',
        './usr/sbin/pppd': 'rwsr-xr--',
        './var/local': 'rwxrwsr-x',
        './var/mail': 'rwxrwsr-x',
        './var/spool/cron/crontabs': 'rwx-wx--T',
        './var/tmp': 'rwxrwxrwt',
    },
    'core16': {
        './bin/mount': 'rwsr-xr-x',
        './bin/ping': 'rwsr-xr-x',
        './bin/ping6': 'rwsr-xr-x',
        './bin/su': 'rwsr-xr-x',
        './bin/umount': 'rwsr-xr-x',
        './etc/chatscripts': 'rwxr-s---',
        './etc/ppp/peers': 'rwxr-s---',
        './run/lock': 'rwxrwxrwt',
        './sbin/pam_extrausers_chkpwd': 'rwxr-sr-x',
        './sbin/unix_chkpwd': 'rwxr-sr-x',
        './tmp': 'rwxrwxrwt',
        './usr/bin/chage': 'rwxr-sr-x',
        './usr/bin/chfn': 'rwsr-xr-x',
        './usr/bin/chsh': 'rwsr-xr-x',
        './usr/bin/crontab': 'rwxr-sr-x',
        './usr/bin/dotlockfile': 'rwxr-sr-x',
        './usr/bin/expiry': 'rwxr-sr-x',
        './usr/bin/gpasswd': 'rwsr-xr-x',
        './usr/bin/mail-lock': 'rwxr-sr-x',
        './usr/bin/mail-unlock': 'rwxr-sr-x',
        './usr/bin/mail-touchlock': 'rwxr-sr-x',
        './usr/bin/newgrp': 'rwsr-xr-x',
        './usr/bin/passwd': 'rwsr-xr-x',
        './usr/bin/ssh-agent': 'rwxr-sr-x',
        './usr/bin/sudo': 'rwsr-xr-x',
        './usr/bin/wall': 'rwxr-sr-x',
        './usr/lib/dbus-1.0/dbus-daemon-launch-helper': 'rwsr-xr--',
        './usr/lib/openssh/ssh-keysign': 'rwsr-xr-x',
        './usr/lib/snapd/snap-confine': 'rwsr-sr-x',
        './usr/local/lib/python3.5': 'rwxrwsr-x',
        './usr/local/lib/python3.5/dist-packages': 'rwxrwsr-x',
        './usr/sbin/pppd': 'rwsr-xr--',
        './var/local': 'rwxrwsr-x',
        './var/mail': 'rwxrwsr-x',
        './var/spool/cron/crontabs': 'rwx-wx--T',
        './var/tmp': 'rwxrwxrwt',
    },
    'core18': {
        './bin/mount': 'rwsr-xr-x',
        './bin/su': 'rwsr-xr-x',
        './bin/umount': 'rwsr-xr-x',
        './sbin/pam_extrausers_chkpwd': 'rwxr-sr-x',
        './sbin/unix_chkpwd': 'rwxr-sr-x',
        './tmp': 'rwxrwxrwt',
        './usr/bin/chage': 'rwxr-sr-x',
        './usr/bin/chfn': 'rwsr-xr-x',
        './usr/bin/chsh': 'rwsr-xr-x',
        './usr/bin/expiry': 'rwxr-sr-x',
        './usr/bin/gpasswd': 'rwsr-xr-x',
        './usr/bin/newgrp': 'rwsr-xr-x',
        './usr/bin/passwd': 'rwsr-xr-x',
        './usr/bin/ssh-agent': 'rwxr-sr-x',
        './usr/bin/sudo': 'rwsr-xr-x',
        './usr/bin/wall': 'rwxr-sr-x',
        './usr/lib/dbus-1.0/dbus-daemon-launch-helper': 'rwsr-xr--',
        './usr/lib/openssh/ssh-keysign': 'rwsr-xr-x',
        './var/local': 'rwxrwsr-x',
        './var/mail': 'rwxrwsr-x',
        './var/tmp': 'rwxrwxrwt',
    },
    'openwrt': {  # demo from Canonical
        './rootfs/tmp': 'rwxrwxrwt',
    },
    'opera': {  # official Opera snap
        './usr/lib/x86_64-linux-gnu/opera-developer/opera_sandbox': 'rwsr-xr-x',
    },
    'opera-beta': {  # official Opera snap
        './usr/lib/x86_64-linux-gnu/opera-developer/opera_sandbox': 'rwsr-xr-x',
    },
    'opera-developer': {  # official Opera snap
        './usr/lib/x86_64-linux-gnu/opera-developer/opera_sandbox': 'rwsr-xr-x',
    },
    'snapd': {
        './usr/lib/snapd/snap-confine': 'rwsr-sr-x',
    },
    'ubuntu-core': {
        './bin/mount': 'rwsr-xr-x',
        './bin/ping': 'rwsr-xr-x',
        './bin/ping6': 'rwsr-xr-x',
        './bin/su': 'rwsr-xr-x',
        './bin/umount': 'rwsr-xr-x',
        './etc/chatscripts': 'rwxr-s---',
        './etc/ppp/peers': 'rwxr-s---',
        './run/lock': 'rwxrwxrwt',
        './sbin/pam_extrausers_chkpwd': 'rwxr-sr-x',
        './sbin/unix_chkpwd': 'rwxr-sr-x',
        './tmp': 'rwxrwxrwt',
        './usr/bin/chage': 'rwxr-sr-x',
        './usr/bin/chfn': 'rwsr-xr-x',
        './usr/bin/chsh': 'rwsr-xr-x',
        './usr/bin/crontab': 'rwxr-sr-x',
        './usr/bin/dotlockfile': 'rwxr-sr-x',
        './usr/bin/expiry': 'rwxr-sr-x',
        './usr/bin/gpasswd': 'rwsr-xr-x',
        './usr/bin/mail-lock': 'rwxr-sr-x',
        './usr/bin/mail-unlock': 'rwxr-sr-x',
        './usr/bin/mail-touchlock': 'rwxr-sr-x',
        './usr/bin/newgrp': 'rwsr-xr-x',
        './usr/bin/passwd': 'rwsr-xr-x',
        './usr/bin/ssh-agent': 'rwxr-sr-x',
        './usr/bin/sudo': 'rwsr-xr-x',
        './usr/bin/wall': 'rwxr-sr-x',
        './usr/lib/dbus-1.0/dbus-daemon-launch-helper': 'rwsr-xr--',
        './usr/lib/openssh/ssh-keysign': 'rwsr-xr-x',
        './usr/lib/snapd/snap-confine': 'rwsr-xr-x',
        './usr/local/lib/python3.5': 'rwxrwsr-x',
        './usr/local/lib/python3.5/dist-packages': 'rwxrwsr-x',
        './usr/sbin/pppd': 'rwsr-xr--',
        './var/local': 'rwxrwsr-x',
        './var/mail': 'rwxrwsr-x',
        './var/spool/cron/crontabs': 'rwx-wx--T',
        './var/tmp': 'rwxrwxrwt',
    },
}

# Snaps that may specify 'daemon' with 'browser-support'. Normally this
# shouldn't be granted because snaps running with 'daemon' run as root and this
# grants more privileges than intended.
sec_browser_support_overrides = ['chromium-mir-kiosk',
                                 'screencloudplayer',
                                 'webdemo',
                                 ]

# Snaps that for some reason do not resquash properly. This is primarily used
# for partners that are stuck on an older snapcraft.
sec_resquashfs_overrides = ['clion',  # jetbrains
                            'clion-nsg',
                            'datagrip',
                            'gogland',
                            'goland',
                            'intellij-idea-community',
                            'intellij-idea-ultimate',
                            'kotlin',
                            'kotlin-native',
                            'phpstorm',
                            'pycharm-community',
                            'pycharm-educational',
                            'pycharm-professional',
                            'rider',
                            'rubymine',
                            'webstorm',  # end jetbrains
                            ]
# Snaps that have legitimate need for executable stack but otherwise work fine
# in strict mode
func_execstack_overrides = ['checkbox-balboa',
                            'checkbox-oem-qa',
                            'checkbox-plano',
                            'checkbox-plano-classic',
                            'checkbox-snappy',
                            'checkbox-tillamook',
                            'store-checker',
                            'enemy-territory',
                            ]

# Some files from staged packages are known to have execstack, so don't flag
# snaps with these since they may have incidentally included them. IMPORTANT:
# some files in the archive have execstack but should have it stripped, so
# don't include those here.
func_execstack_skipped_pats = ['boot/.*',
                               'lib/klibc.*',
                               'usr/bin/.*-mingw.*-gnat.*',
                               'usr/bin/gnat.*',
                               'usr/bin/.*gnat.*-[0-9]$',
                               'usr/bin/grub.*',
                               'usr/lib/debug/.*',
                               'usr/lib/grub/.*',
                               'usr/lib/libatlas-test/.*',
                               'usr/.*/libgnat.*',
                               'usr/lib.*/.*nvidia.*',
                               'usr/lib/syslinux/modules/.*',
                               'usr/share/dpdk/test/.*',
                               # investigate
                               'usr/lib/arm-linux-gnueabihf/libx264.so.148',
                               'usr/lib/arm-linux-gnueabihf/libvolk.so.1.1',
                               ]

# By default we don't regulate which snaps specify which base snaps, but some
# base snaps are highly specialized, so we limit what can use them. Base snaps
# whose name is not a key in this dict don't flag for review. For base snaps
# whose name is a key in this dict, snaps not listed in the list for the base
# snap are flagged for manual review.
# https://forum.snapcraft.io/t/manual-review-of-base-snaps/2839/9
lint_redflagged_base_dep_override = {
    'solus-runtime-gaming': [
        'linux-steam-integration',
    ],
}

# Some publisher_emails represent a shared account. For snaps with a shared
# email, also send to other addresses.
canonical_desktop = ['ken.vandine@canonical.com',
                     'sebastien.bacher@canonical.com',
                     'will.cooke@canonical.com',
                     ]

canonical_enablement = ['snappy-canonical-enablement@canonical.com']

canonical_foundations = ['daniel.watkins@canonical.com',
                         'patricia.gaughen@canonical.com',
                         'steve.langasek@canonical.com',
                         ]

canonical_kernel = ['brad.figg@canonical.com',
                    'leann.ogasawara@canonical.com',
                    'tyler.hicks@canonical.com',
                    ]

canonical_hwe = ['anthony.wong@canonical.com',
                 'leann.ogasawara@canonical.com',
                 ]

canonical_juju = ['ian.booth@canonical.com',
                  'tim.penhey@canonical.com',
                  ]

canonical_k8s = ['adam.stokes@canonical.com',
                 'tim.van.steenburgh@canonical.com',
                 ]

canonical_lxd = ['david.britton@canonical.com',
                 'stephane.graber@canonical.com',
                 'tyler.hicks@canonical.com',
                 ]

canonical_mir = ['alan.griffiths@canonical.com',
                 'gerry.boland@canonical.com',
                 'michal.sawicz@canonical.com',
                 ]

canonical_multipass = canonical_mir

canonical_security = ['emily.ratliff@canonical.com',
                      'jamie@canonical.com',
                      ]

canonical_server = ['david.britton@canonical.com',
                    'robie.basak@canonical.com',
                    ]

canonical_snapd = ['gustavo.niemeyer@canonical.com',
                   'michael.vogt@canonical.com',
                   ]

canonical_snapcraft = ['evan.dandrea@canonical.com',
                       'sergio.schvezov@canonical.com',
                       ]

# snaps@canonical.com used to be 'snappy-canonical-storeaccount@canonical.com'
# but it was changed a little while ago
update_publisher_overrides = {
    'snaps@canonical.com': {
        'aws-kernel': canonical_kernel,
        'azure-kernel': canonical_kernel,
        'base-18': canonical_snapd,
        'bluez': canonical_enablement,
        'caracalla-kernel': canonical_hwe,
        'chromium': ['olivier.tilloy@canonical.com'] + canonical_desktop,
        'chromium-ffmpeg': ['olivier.tilloy@canonical.com'] + canonical_desktop,
        'chromium-mir-kiosk': ['olivier.tilloy@canonical.com'] + canonical_mir,
        'conjure-up': canonical_k8s,
        'core': canonical_snapd,
        'core16': canonical_snapd,
        'core18': canonical_snapd,
        'dell-edge-iot-kernel': canonical_kernel,
        'dragonboard-kernel': canonical_kernel,
        'eog': canonical_desktop,
        'gcp-kernel': canonical_kernel,
        'gedit': canonical_desktop,
        'git-ubuntu': canonical_server,
        'gke-kernel': canonical_kernel,
        'gnome-3-26-1604': canonical_desktop,
        'gnome-3-28-1804': canonical_desktop,
        'gnome-calculator': canonical_desktop,
        'gnome-calendar': canonical_desktop,
        'gnome-characters': canonical_desktop,
        'gnome-clocks': canonical_desktop,
        'gnome-contacts': canonical_desktop,
        'gnome-dictionary': canonical_desktop,
        'gnome-logs': canonical_desktop,
        'gnome-sudoku': canonical_desktop,
        'gnome-system-monitor': canonical_desktop,
        'godd': canonical_snapd,
        'juju': canonical_juju,
        'jq': canonical_snapd,
        'jq-core18': canonical_snapd,
        'libreoffice': canonical_desktop,
        'lxd': canonical_lxd,
        'microk8s': canonical_k8s,
        'mir-kiosk': canonical_mir,
        'mir-kiosk-apps': canonical_mir,
        'modem-manager': canonical_enablement,
        'multipass': canonical_multipass,
        'network-manager': canonical_enablement,
        'pc': canonical_snapd,
        'pc-kernel': canonical_kernel,
        'pi2-kernel': canonical_kernel,
        'quadrapassel': canonical_desktop,
        'simple-scan': canonical_desktop,
        'smt': canonical_security,
        'snapcraft': canonical_snapcraft,
        'snapd': canonical_snapd,
        'snappy-debug': canonical_security,
        'snapweb': canonical_enablement,
        'stlouis-kernel': canonical_hwe,
        'strace-static': canonical_snapd,
        'subiquity': canonical_foundations,
        'test-snapd-accounts-service': canonical_snapd,
        'test-snapd-autopilot-consumer': canonical_snapd,
        'test-snapd-busybox-static': canonical_snapd,
        'test-snapd-cups-control-consumer': canonical_snapd,
        'test-snapd-dbus-consumer': canonical_snapd,
        'test-snapd-dbus-provider': canonical_snapd,
        'test-snapd-eds': canonical_snapd,
        'test-snapd-fuse-consumer': canonical_snapd,
        'test-snapd-go-webserver': canonical_snapd,
        'test-snapd-gpio-memory-control': canonical_snapd,
        'test-snapd-gsettings': canonical_snapd,
        'test-snapd-hello-classic': canonical_snapd,
        'test-snapd-kernel-module-consumer': canonical_snapd,
        'test-snapd-location-control-provider': canonical_snapd,
        'test-snapd-network-status-provider': canonical_snapd,
        'test-snapd-openvswitch-support': canonical_snapd,
        'test-snapd-password-manager-consumer': canonical_snapd,
        'test-snapd-physical-memory-control': canonical_snapd,
        'test-snapd-python-webserver': canonical_snapd,
        'test-snapd-rsync-core18': canonical_snapd,
        'test-snapd-system-observe-consumer': canonical_snapd,
        'test-snapd-uhid': canonical_snapd,
        'test-snapd-upower-observe-consumer': canonical_snapd,
        'ubuntu-image': canonical_foundations,
        'ufw': canonical_security,
        'wifi-ap': canonical_enablement,
        'wifi-connect': canonical_enablement,
    },
}

# Some binary packages aren't worth alerting on since they don't contain
# affected binaries (eg, a package with only header files)
update_binaries_ignore = ['linux-headers-generic',
                          'linux-libc-dev',
                          ]

# Some snaps may have legitimate access for external symlinks. This only says
# that some symlink may point to this target. It does not verify the name of
# the symlink (only the target).
common_external_symlink_override = {
    'snapd': ['usr/lib/snapd/snap-device-helper'],
}
