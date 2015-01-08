# ExpiredIPA

This script sends an email to users whose password is about to expire. It provides a link to our IPA instance as well as a GIF showing how to reset your password. Additionally, it sends a small report to administrators notifying them whose passwords are expired as well as users that are disabled.

## Usage
The script can be run standalone or by cron. When using cron and a virtual environment I had to use the following command:

> echo 'source /home/username/.venv/ExpiredIPA/bin/activate; python /home/username/scripts/ExpiredIPA/expired.py > /tmp/cronlog_ExpiredIPA.txt 2>&1' | /bin/bash
