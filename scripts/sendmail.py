#!/usr/bin/env q-python27
# -*- coding: utf-8 -*-

import time
import smtplib
from email.mime.text import MIMEText

def sendMail(sender, receiver, subject, text):
    email_body              = MIMEText(text, "plain", "UTF-8")
    email_body['Subject']   = u"%s" % subject
    email_body['From']      = sender
    email_body['To']        = receiver
    try:
        mail_sender = smtplib.SMTP()
        mail_sender.connect("mail.qunar.com")
        mail_sender.sendmail(sender, receiver, email_body.as_string())
        mail_sender.close()
        return True
    except Exception, e:
        return False

if __name__ == '__main__':
    cnt = 0
    while True:
        cnt = cnt + 1
        print '[sendmial] %d' % cnt
        sendMail('abc@qunar.com', 'dongliang.ma@qunar.com', "__id %d" % cnt, "dummy")
        time.sleep(5)
