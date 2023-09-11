# -*- coding: utf-8 -*-
"""
实现搜书吧论坛登入和发布空间动态
"""
import os
import re
import sys
from copy import copy

import requests
from bs4 import BeautifulSoup
import time
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

ch = logging.StreamHandler(stream=sys.stdout)
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)
def sendmsg(msg):
    data = {
        "qq": "1351714146",
        "msg": msg,
    }
    requests.post('http://home.undem.cn:6789/send/bf89f9759a9478d2979fd6ab13152fc6',data=data)
def geturl(x):
    a = requests.get(x)
    if (len(a.text)<20000):
        while(len(a.text)<2000):
            url=re.findall('url=(.*?)"></html>',a.text)
            a=requests.get(url[0])
        a.encoding = a.apparent_encoding
        raw=a.text
        link=re.findall('<p><a href="https://(.*?)/" target="_blank">搜书吧入口</a></p>',raw)
        return(link[0])
    else:
        x=re.findall('https://(.*?)/',x)[0]
        return x
class SouShuBaClient:

    def __init__(self, hostname: str, username: str, password: str, questionid: str = '0', answer: str = None,
                 proxies: dict =None):
        self.session: requests.Session = requests.Session()
        self.hostname = hostname
        self.username = username
        self.password = password
        self.questionid = questionid
        self.answer = answer
        self._common_headers = {
            "Host": f"{ hostname }",
            "Connection": "keep-alive",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Accept-Language": "zh-CN,cn;q=0.9",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        self.proxies = proxies

    def login_form_hash(self):
        rst = self.session.get(f'https://{self.hostname}/member.php?mod=logging&action=login').text
        loginhash = re.search(r'<div id="main_messaqge_(.+?)">', rst).group(1)
        formhash = re.search(r'<input type="hidden" name="formhash" value="(.+?)" />', rst).group(1)
        return loginhash, formhash

    def login(self, ):
        """Login with username and password"""
        loginhash, formhash = self.login_form_hash()
        login_url = f'https://{self.hostname}/member.php?mod=logging&action=login&loginsubmit=yes' \
                    f'&handlekey=register&loginhash={loginhash}&inajax=1'


        headers = copy(self._common_headers)
        headers["origin"] = f'https://{self.hostname}'
        headers["referer"] = f'https://{self.hostname}/'
        payload = {
            'formhash': formhash,
            'referer': f'https://{self.hostname}/',
            'username': self.username,
            'password': self.password,
            'questionid': self.questionid,
            'answer': self.answer
        }

        resp = self.session.post(login_url, proxies=self.proxies, data=payload, headers=headers)
        if resp.status_code == 200:
            logger.info(f'Welcome {self.username}!')
        else:
            raise ValueError('Verify Failed! Check your username and password!')
    def getcoin(self):
        headers = copy(self._common_headers)
        headers["origin"] = f'https://{self.hostname}'
        headers["referer"] = f'https://{self.hostname}/'
        resp=self.session.get('https://downdown.downdownbook.com/home.php?mod=spacecp&ac=credit&op=base',headers=headers)
        coin=re.findall('<li class="xi1 cl"><em> 银币: </em>(.*?)  &nbsp; </li>',resp.text)
        return coin[0]
    def credit(self):
        credit_url = f"https://{self.hostname}/home.php?mod=spacecp&ac=credit&showcredit=1&inajax=1&ajaxtarget=extcreditmenu_menu"

        credit_rst = self.session.get(credit_url).text
        credit_soup = BeautifulSoup(credit_rst, "lxml")
        hcredit_2 = credit_soup.find("span", id="hcredit_2").string

        return hcredit_2

    def space_form_hash(self):
        rst = self.session.get(f'https://{self.hostname}/home.php').text
        formhash = re.search(r'<input type="hidden" name="formhash" value="(.+?)" />', rst).group(1)
        return formhash

    def space(self):
        formhash = self.space_form_hash()
        space_url = f"https://{self.hostname}/home.php?mod=spacecp&ac=doing&handlekey=doing&inajax=1"

        headers = copy(self._common_headers)
        headers["origin"] = f'https://{self.hostname}'
        headers["referer"] = f'https://{self.hostname}/'

        for x in range(5):
            payload = {
                "message": "开心赚银币 {0} 次".format(x + 1).encode("GBK"),
                "addsubmit": "true",
                "spacenote": "true",
                "referer": "home.php",
                "formhash": formhash
            }
            resp = self.session.post(space_url, proxies=self.proxies, data=payload, headers=headers)
            if re.search("操作成功", resp.text):
                logger.info(f'{self.username} post {x + 1}nd successfully!')
                time.sleep(120)
            else:
                logger.warning(f'{self.username} post {x + 1}nd failed!')


if __name__ == '__main__':
    try:
        # client = SouShuBaClient(os.environ.get('SOUSHUBA_HOSTNAME', 'www.apr.soushu2029.com'),
        #                         os.environ.get('SOUSHUBA_USERNAME'),
        #                         os.environ.get('SOUSHUBA_PASSWORD'))
        client = SouShuBaClient(geturl(os.environ.get('SOUSHUBA_HOSTNAME', 'http://soushu2023.com/')),
                                 os.environ.get('SOUSHUBA_USERNAME'),
                                 os.environ.get('SOUSHUBA_PASSWORD'))
        client.login()
        client.space()
        coin=client.getcoin()
        sendmsg("今日7枚银币已经成功获取,当前银币总数："+coin)
        credit = client.credit()
    except Exception as e:
        logger.error(e)
        sys.exit(1)
