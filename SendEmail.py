
# -*- coding: utf-8 -*-

# Send email
# 2017-11-29

import re
import os
import uuid
import random
import smtplib
import base64

from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from email.header import Header
from mimetypes import guess_type

# 接收人类型定义
EMAIL_RECEIVER_TO  = 0
EMAIL_RECEIVER_CC  = 1
EMAIL_RECEIVER_BCC = 2
EMAIL_RECEIVER_SC  = 3

# 加密类型定义
EMAIL_SMTP_TEXT    = 0
EMAIL_SMTP_TLS     = 1
EMAIL_SMTP_SSL     = 2

class smtp_email:
    def __init__(self, _sender, _pwd, _host, _port=0):
        self.__sender   = _sender   # 用户名
        self.__pwd      = _pwd      # 密码
        self.__host     = _host     # smtp服务器
        self.__port     = _port     # smtp端口

        self.__receiver = []        # 收件人列表
        self.__title    = ""        # 邮件标题
        self.__content  = ""        # 邮件内容
        self.__quote    = []        # 引用列表
        self.__attach   = []        # 附件列表

        self.__to       = []        # 收件人
        self.__cc       = []        # 抄送
        self.__bcc      = []        # 密送
        self.__uuid     = uuid.uuid4()
        self.__qnum     = random.randint(100000, 999999)

        self.__re = re.compile("^[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$")

    # type: 0-收件人，1-抄送，2-暗抄送，3-密送
    def add_receiver(self, _receiver, _type=EMAIL_RECEIVER_TO):
        if isinstance(_receiver, list):
            for x in _receiver:
                self.add_receiver(x, _type)
        elif isinstance(_receiver, str):
            # 正则判断是否为邮箱
            if None != self.__re.match(_receiver):
                if _type == EMAIL_RECEIVER_TO:
                    self.__to.append(_receiver)
                elif _type == EMAIL_RECEIVER_CC:
                    self.__cc.append(_receiver)
                elif _type == EMAIL_RECEIVER_BCC:
                    self.__bcc.append(_receiver)
                elif _type != EMAIL_RECEIVER_SC:
                    print("receiver type unknown.")
                    return

                self.__receiver.append(_receiver)
            else:
                print("\"%s\" is not email." % _receiver)
        else:
            print("param is not str or list." % _receiver)

    def set_title(self, _title, _charset='utf-8'):
        if not _charset:
            if all(ord(c) < 128 for c in _title):
                self.__title = Header(_title)
            else:
                self.__title = Header(_title, 'utf-8')
        else:
            self.__title = Header(_title, _charset)

    def set_content(self, _content, _subtype='plain', _charset='utf-8'):
        self.__content = MIMEText(_content, _subtype=_subtype, _charset=_charset)

    def add_content(self, _content, _subtype='plain', _charset='utf-8'):
        if not self.__content:
            self.__content = MIMEText(_content, _subtype=_subtype, _charset=_charset)
        else:
            self.__content.attach(MIMEText(_content, _subtype=_subtype, _charset=_charset))

    def add_attachment(self, _filepath):
        if os.path.isfile(_filepath):
            self.__attach.append(_filepath)
        else:
            print("\"%s\" does not exist." % _filepath)

    def quote_cid(self):
        self.__qnum += 1
        return str(self.__uuid) + "-" + hex(self.__qnum)[-5:]

    def add_quote(self, _filepath, _cid=None):
        cid = _cid if _cid else self.quote_cid()
        self.__quote.append((cid, _filepath))
        return cid

    def send(self, _enc_type=EMAIL_SMTP_SSL):
        if (self.__sender == "" or self.__host == "" or len(self.__receiver) == 0):
            return False

        try:
            _msg_root = MIMEMultipart('related')
            _msg_alte = MIMEMultipart('alternative')
            _msg_root.attach(_msg_alte)

            _msg_root['Subject'] = self.__title
            _msg_root['From'] = self.__sender

            if len(self.__to) > 0:
                _msg_root['To'] = '<' + '>, \r\n\t<'.join(self.__to) + '>'
            if len(self.__cc) > 0:
                _msg_root['Cc'] = '<' + '>, \r\n\t<'.join(self.__cc) + '>'
            if len(self.__bcc) > 0:
                _msg_root['Bcc'] = '<' + '>, \r\n\t<'.join(self.__bcc) + '>'

            _msg_root.attach(self.__content)

            for quote in self.__quote:
                cid = '<' + quote[0] + '>'
                (mimetype, encoding) = guess_type(quote[1])
                if not mimetype:
                    raise Exception("Could not guess [%s] MIME subtype." % quote[1])
                (maintype, subtype) = mimetype.split('/')
                with open(quote[1], 'rb') as fp:
                    quote_msg = MIMEImage(fp.read(), _subtype=maintype)
                    quote_msg.add_header('Content-ID', cid)
                    _msg_root.attach(quote_msg)

            if self.__attach:
                _msg_alte = MIMEMultipart('alternative')
                _msg_root.attach(_msg_alte)
                for _path in self.__attach:
                    _part = MIMEApplication(open(_path, 'rb').read())
                    _part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(_path))
                    _msg_alte.attach(_part)

            _s = smtplib.SMTP_SSL() if _enc_type == EMAIL_SMTP_SSL else smtplib.SMTP()
            _s.connect(host=self.__host, port=self.__port)
            #_s.ehlo()
            if _enc_type == EMAIL_SMTP_TLS:    _s.starttls()
            _s.login(self.__sender, self.__pwd)
            _s.sendmail(self.__sender, self.__receiver, _msg_root.as_string())
            _s.quit()
            #_s.close()
            return True
        except Exception as e:
           if isinstance(e, smtplib.SMTPResponseException):
               print(str(e))
           else:
               print(e) #python3    python2:print(e.message)
        return False


def main():
    _smtp = smtp_email("xxxxxxxx@163.com", "xxxxxxxx", "smtp.163.com")
    _smtp.set_title("test pythen send email")
    _smtp.set_content("test content")
    _smtp.add_receiver(["yyyyyy@163.com","zzzzzz@163.com"])
    #_smtp.add_attachment("111.jpg")
    # html = '<img src="cid:%s">' % _smtp.add_quote("111.jpg")
    # _smtp.add_content(html, 'html')
    if _smtp.send():
        print("send email succeed.")
    else:
        print("send email failed.")
 
if __name__ == '__main__':
    main()
