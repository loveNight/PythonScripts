#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: LostInNight
# @Date:   2015-10-27 14:31:20
# @Last Modified by:   LostInNight
# @Last Modified time: 2015-11-11 09:04:36

# 本脚本用于切换公司后台登陆账号

from selenium import webdriver
import os
import threading


def main(username, password):
    browser = webdriver.Chrome()
    # 在指定时间范围等待：
    browser.implicitly_wait(30)

    # 设置超时
    browser.set_page_load_timeout(30)
    browser.set_script_timeout(30)

    browser.get(r'http://公司网站')

    text_username = browser.find_element_by_name('username')
    text_password = browser.find_element_by_name('password')
    form_login = browser.find_element_by_name('formlogin')

    text_username.send_keys(username)
    text_password.send_keys(password)
    form_login.submit()  # 登录

    # 跳转到登录后打开的新标签
    window = browser.window_handles
    browser.switch_to_window(window[1])
    # 点击 数据管理
    browser.find_element_by_partial_link_text('数据管理').click()
    # 点击 VIP会员管理
    vip = browser.find_element_by_id('minfo_33412')
    vip.click()
    return browser


if __name__ == '__main__':
    user_type = input('请输入你要登录的账号类型：')
    if not user_type:
        print('输入错误，程序结束！')
        exit(1)
    if user_type == '账号1':
        file = r'd:需要和账号1同时打开的文件'
        threading.Thread(
            target=lambda file: os.system(file), args=(file,)).start()
        browser = main('账号1', '密码1')
    elif user_type == 'wdn':
        main('账号2', '密码2')
    elif user_type in ['账号3', '账号3的别名']:
        main('账号3', '密码3')
