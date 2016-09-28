#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: LostInNight
# @Date:   2015-11-02 10:56:58
# @Last Modified by:   LostInNight
# @Last Modified time: 2015-11-19 15:20:12


# 生意社报价审核的脚本
import requests
import os
import datetime
import sys
import configparser
from bs4 import BeautifulSoup as BS
import time


class Client(object):

    """自动审核XXXXXXXXXXX报价

    需要在同目录下有配置文件，格式：


    [user]
    username = XXXXXXXXX
    password = XXXXXXXXXXXXXX

    [price_accounts]
    XXXXXXXXX = XXXXXXXXX
    XXXXXXXXX = XXXXXXXXX
    XXXXXXXXX = XXXXXXXXX
    XXXXXXXXX = XXXXXXXXX
    XXXXXXXXX = XXXXXXXXX
    """

    CONFIG_FILE = "XXXXXXXXXX.ini"  # 配置文件
    LOGIN_URL = r'http://XXXXXXXXXXXXXXXogin_form'
    PRICE_URL = r'http://XXXXXXXXXXXXXXXXXXXXX'
    ACTIVATE_URL = r'http://XXXXXXXXXXXXXXX'
    HEADERS = {
        'Accept-Encoding': 'gzip, deflate',
        'Host': 'XXXXXXXXXX.com',
        'Origin': 'http://XXXXXXXXXXXX.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.71 Safari/537.36'
    }
    DEBUG = True  # 开关调试信息

    def __init__(self):
        os.chdir(sys.path[0])
        self.session = requests.Session()
        self._read_config_file()

    def start(self):
        self._login()
        while True:
            for account in self.accounts:
                self._check_inactive_price(account)
            time.sleep(60)

    def _read_config_file(self):
        config = configparser.ConfigParser()
        config.read(Client.CONFIG_FILE, encoding="utf-8")
        self.username = config.get("user", "username")
        self.password = config.get("user", "password")
        self.accounts = config.options("price_accounts")
        self._log("取出待审核账号：\n%s" % "\n".join(self.accounts))

    def _log(self, message):
        if Client.DEBUG:
            now = str(datetime.datetime.now())
            index = now.rfind(":")
            now = now[:index + 3]
            message = message.encode("gbk", errors="ignore").decode("gbk")
            print("-" * 50)
            print("%s" % now)
            print(message + "\n")

    def _login(self):
        data = {
            'f': 'check_login',
            'username': self.username,
            'password': self.password,
            'f1': ''
        }
        html = self.session.post(
            Client.LOGIN_URL, data=data, headers=Client.HEADERS)
        # 失败则返回网址'http://XXXXXXXXXXXXXndex.php?f=login_form&error=1'
        # 成功则返回网址'http://XXXXXXXXXXXXXXndex.php?f=welcome'
        assert 'welcome' in html.url, "登录错误！请检查账号"
        self._log('登录 %s 成功！' % self.username)

    def _open_url(self, url):
        return self.session.get(url).text

    def _activate_price(self, price_id):
        post_data = {
            'f': 'change_price_status',
            "welcome": "no",
            "id": price_id
        }
        self.session.post(Client.ACTIVATE_URL, data=post_data)

    def _check_inactive_price(self, account):
        html = self._open_url(Client.PRICE_URL.format(account))
        soup = BS(html, "lxml")
        table = soup.table
        trs = table.find_all("tr")  # 所有<tr>标签
        data_trs = trs[1:-1]  # 首尾两行没报价数据
        for index, tr in enumerate(data_trs):
            tds = tr.find_all("td")
            if index % 2 == 0:
                goods = tds[0].string  # 商品名称
                price_type = tds[1].string  # 报价类型
                price = tds[3].string  # 现货价格
                date = tds[4].string  # 报价日期
                price_id = tds[5].a["rel"][0]  # 用于激活
            else:
                attrs = tds[1].string  # 属性与规格
                attrs = ["", attrs][attrs != None]  # None则显示空白
                self._log("检测到账号 %s 的新报价：\n" % account +
                          " ".join([goods, price_type, price, date, attrs]))
                self._activate_price(price_id)
                self._log("已激活上述报价！")


if __name__ == '__main__':
    sout = Client().start()
