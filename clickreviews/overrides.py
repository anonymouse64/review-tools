'''overrides.py: overrides for various functions'''
#
# Copyright (C) 2017 Canonical Ltd.
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
               'freescale-ls1043a-kernel',
               'gcp-kernel',
               'gke-kernel',
               'hummingboard-kernel',
               'joule-linux',
               'joule-linux-lool',
               'linux-generic-allwinner',
               'mako-kernel',
               'marvell-armada3700-kernel',
               'nxp-ls1043a-kernel',
               'odroidxu4-kernel',
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
    'gadget': ['dragonboard',  # Canonical reference gadgets
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
    'base': ['bare',            # Canonical base snaps
             'test-snapd-base',
             ],
}

# List of snaps that may specify an interface that requires a desktop file but
# not supply a desktop file itself.
desktop_file_exception = ['ffscreencast',
                          'pulsemixer',
                          ]

#
# sr_security.py overrides
#
# Files with unusual that we'll allow for certain snaps
sec_mode_overrides = {
    'bare': {},
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
        './usr/lib/snapd/snap-confine': 'rwsr-xr-x',
        './usr/local/lib/python3.5': 'rwxrwsr-x',
        './usr/local/lib/python3.5/dist-packages': 'rwxrwsr-x',
        './usr/sbin/pppd': 'rwsr-xr--',
        './var/local': 'rwxrwsr-x',
        './var/mail': 'rwxrwsr-x',
        './var/spool/cron/crontabs': 'rwx-wx--T',
        './var/tmp': 'rwxrwxrwt',
    },
    'chrome-test': {  # chrome-test from Canonical
        './opt/google/chrome/chrome-sandbox': 'rwsr-xr-x',
    },
    'chromium': {  # chromium from Canonical
        './usr/lib/chromium-browser/chrome-sandbox': 'r-sr-xr-x',
    },
    'openwrt': {  # demo from Canonical
        './rootfs/tmp': 'rwxrwxrwt',
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
sec_browser_support_overrides = ['screencloudplayer',
                                 'webdemo']

# Snaps that have legitimate need for executable stack but otherwise work fine
# in strict mode
func_execstack_overrides = []

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
                               ]
