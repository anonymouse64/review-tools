'''email.py: classes for email module'''
# Copyright (C) 2018 Canonical Ltd.
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

from email.mime.text import MIMEText
from email.utils import parseaddr
import os
import smtplib
import sys

# The From address for all emails
email_from_addr = "Snap Store <noreply@canonical.com>"

# Send via local SMTP server
email_server = 'localhost'


def sanitize_addr(addr):
    '''Roughly sanitize the email field'''
    (name, email) = parseaddr(addr)

    # "Foo bar <bad>"
    if '@' not in email:
        return ''

    # "Foo bar <bad@>", "Foo bar <bad@@bad>", "Foo bar <@bad>"
    if email.count('@') == 1 and (email.startswith('@') or
                                  email.endswith('@')):
        return ''

    return email


def send(email_to_addr, subj, body):
    '''Send the email'''
    global email_server
    global email_from_addr

    if 'CRT_SEND_EMAIL' not in os.environ or \
            os.environ['CRT_SEND_EMAIL'] != "1":
        print("From: %s\nTo: %s\nSubject: %s\n" % (email_from_addr,
                                                   email_to_addr,
                                                   subj))
        print(body)
    else:
        if 'CRT_EMAIL_FROM' in os.environ:
            email_from_addr = sanitize_addr(os.environ['CRT_EMAIL_FROM'])
            if email_from_addr == '':
                print("Bad from address: '%s'" % email_from_addr)
                return False
        if 'CRT_EMAIL_TO' in os.environ:
            email_to_addr = sanitize_addr(os.environ['CRT_EMAIL_TO'])
            if email_to_addr == '':
                print("Bad to address: '%s'" % email_to_addr)
                return False
        if 'CRT_EMAIL_SERVER' in os.environ:
            email_server = os.environ['CRT_EMAIL_SERVER']

        if 'CRT_EMAIL_NOPROMPT' not in os.environ or \
                os.environ['CRT_EMAIL_NOPROMPT'] != "1":
            print("Send (subj='%s',to='%s',from='%s',server='%s')? (y|N) " %
                  (subj, email_to_addr, email_from_addr, email_server), end='')
            sys.stdout.flush()
            ans = sys.stdin.readline().lower().strip()
            if ans != 'y' and ans != 'yes':
                print("aborting email delivery for 'Subject: %s'" % subj)
                return False

        # This can throw many exceptions so the caller needs to catch them and
        # skip updating seen_db
        msg = MIMEText(body)
        msg['Subject'] = subj
        msg['From'] = email_from_addr
        msg['To'] = email_to_addr
        s = smtplib.SMTP(email_server)
        s.send_message(msg)
        s.quit()

    return True
