# -*- coding: utf-8 -*-
"""
实现搜书吧论坛登入和发布空间动态
"""
import re
import sys
from copy import copy

import requests
from bs4 import BeautifulSoup
import time
import logging

import config as cfg

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

ch = logging.StreamHandler(stream=sys.stdout)
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)


class SouShuBaClient:

    def __init__(self, hostname: str, proxies: dict | None = None):
        self.session: requests.Session = requests.Session()
        self.hostname = hostname
        self._common_headers = {
            "Host": f"{ hostname }",
            "Connection": "keep-alive",
            "Accept": "*/*",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Accept-Language": "zh-CN,cn;q=0.9",
        }
        self.proxies = proxies

        self.username = None

    def login_form_hash(self):
        rst = self.session.get(f'https://{self.hostname}/member.php?mod=logging&action=login').text
        loginhash = re.search(r'<div id="main_messaqge_(.+?)">', rst).group(1)
        formhash = re.search(r'<input type="hidden" name="formhash" value="(.+?)" />', rst).group(1)
        return loginhash, formhash

    def login(self, username: str, password: str, questionid: str = '0', answer: str = None):
        """Login with username and password"""
        loginhash, formhash = self.login_form_hash()
        login_url = f'https://{self.hostname}/member.php?mod=logging&action=login&loginsubmit=yes&loginhash={loginhash}&inajax=1'

        headers = copy(self._common_headers)
        headers["origin"] = f'https://{self.hostname}'
        headers["referer"] = f'https://{self.hostname}/'
        payload = {
            'formhash': formhash,
            'referer': f'https://{self.hostname}/',
            'loginfield': username,
            'username': username,
            'password': password,
            'questionid': questionid,
            'answer': answer,
            'cookietime': 2592000
        }

        resp = self.session.post(login_url, proxies=self.proxies, data=payload, headers=headers)
        if resp.status_code == 200 and self.session.cookies.get('yj0M_ada2_auth'):
            self.username = username
            logger.info(f'{username} 登录成功!\n20%')
        else:
            raise ValueError('Verify Failed! Check your username and password!')

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
        headers["Content-Type"] = 'application/x-www-form-urlencoded'

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
                logger.info(f'{self.username} 发布第 {x + 1} 次空间动态成功!\n{int(100 * (3 + x) / 10)}%')
                time.sleep(120)
            else:
                raise ValueError(f'{self.username} 发布第 {x + 1} 次空间动态失败!')


if __name__ == '__main__':
    try:
        client = SouShuBaClient('waterfire.allbookdown.com')
        client.login(cfg.username, cfg.password)
        client.space()
        credit = client.credit()
        logger.info('{0}\n100%\n{{ "complete": 1, "code": 0, "description": "{0}" }}'.format(
            f"{cfg.username} 现在拥有 {credit} 枚银币。"))
    except Exception as e:
        logger.error(e)
        logger.info('{0}\n100%\n{{ "complete": 0, "code": 1, "description": "{0}" }}'.format(e))
        sys.exit(1)
