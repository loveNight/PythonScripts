#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: LostInNight
# @Date:   2015-11-06 11:21:41
# @Last Modified by:   LostInNight
# @Last Modified time: 2015-11-19 15:47:49

"""
下载人人网指定用户的所有相册
需要手动获取uid

uid说明
    用户主页为：http://www.renren.com/123456789/profile
    网页中的123456789即为该用户的uid

目前已经可以完成下载，加了最简陋的多线程

有空时再改进：
1.添加线程池
2.分离抓取与解析
"""

__author__ = "LostInNight"
import requests
from bs4 import BeautifulSoup as BS
from datetime import datetime
import pdb
import sys
import os
from multiprocessing import Queue
import threading
import re
from collections import Counter
import time

# 公共变量
re_filename = re.compile(r'[\/:*?"<>]')
re_uid_in_albums_url = re.compile(r'id=(\d+)&')
re_max_page = re.compile(r'/(\d+)页')

home_url = r"http://3g.renren.com/"
login_url = r"http://3g.renren.com/login.do?autoLogin=true&"
# 用户主页，参数：uid
user_url_pattern = r"http://3g.renren.com/profile.do?id={0}"
# 相册列表，参数：0开始的页码、uid
albums_url_pattern = r"http://3g.renren.com/album/wmyalbum.do?curpage={0}&id={1}"
# 照片列表，参数：0开始的页码、相册id、uid
photos_url_pattern = r"http://3g.renren.com/album/wgetalbum.do?curpage={0}&id={1}&owner={2}"

albums_queue = Queue()  # 每个元素为Album对象
photos_queue = Queue()  # 每个元素为Photo对象

s = requests.Session()
debug = True
delay = 3  # 网络请求间隔，避免太快被拒
lock = threading.Lock()


def log(message):
    if debug:
        lock.acquire()
        try:
            now = str(datetime.now())
            index = now.rfind(":")
            now = now[:index + 3]
            print("\n%s" % now)
            if isinstance(message, str):
                message.encode("gbk", errors="ignore").decode("gbk")
            print(message)
        finally:
            lock.release()


def main(username, password, uid, filepath):
    """脚本方法入口

    username 登录用户名
    password 密码
    uid 待下载的用户的uid

    uid说明
        用户主页为：http://www.renren.com/123456789/profile
        网页中的123456789即为该用户的uid
    """
    start_time = time.time() # 开始计时
    login(username, password)
    target_user_name = get_target_user_name(uid)  # 对方的人人网名，用作文件夹
    filepath = os.path.join(filepath, target_user_name)
    if not os.path.isdir(filepath):
        os.mkdir(filepath)
    resolve_albums_queue(uid) #解析出相册列表

    threads = []
    while not albums_queue.empty():
        album = albums_queue.get()
        t = threading.Thread(target=resolve_photos_queue, args=(album,))
        t.start()
        threads.append(t)
    for x in threads:
        x.join()

    log("一共 %s 张照片" % photos_queue.qsize())
    log("开始下载")

    threads.clear()
    while not photos_queue.empty():
        photo = photos_queue.get()
        t = threading.Thread(target=down_photo, args=(photo, filepath))
        t.start()
        threads.append(t)
    for x in threads:
        x.join()

    used_time = trans_time(time.time() - start_time)
    log("下载完成，耗时：%s，请查看 %s" % (used_time, filepath))


def get(url, binary=False):
    """get请求，binary表示是否返回二进制数据"""
    time.sleep(delay)
    res = s.get(url)
    if binary:
        return res.content
    return res.text


def login(username, password):
    """登录手机人人网"""
    # 打开网页获取登录所需数据
    html = get(home_url)
    soup = BS(html, "lxml")
    lbskey = soup.find("input", {"name": "lbskey"})["value"]
    log("登录用的lbskey:%s" % lbskey)
    post_data = {
        "origURL": "",
        "lbskey": lbskey,
        "c": "",
        "pq": "",
        "appid": "",
        "ref": "http://m.renren.com/q.do?null",
        "email": username,
        "password": password,
        "login": "登录"
    }
    headers = {
        "Host": "3g.renren.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.71 Safari/537.36"
    }
    html = s.post(login_url, data=post_data, headers=headers)
    # 失败返回网址：http://3g.renren.com/login.do?autoLogin=true&
    # 成功跳到网址：http://3g.renren.com/home.do?sid........
    if "请输入密码和验证码后登录" in html.text:
        verify_file = os.path.join(sys.path[0], "verify.jpg")
        soup = BS(html.text, "lxml")
        verifykey = soup.find(
            "input", {"type": "hidden", "name": "verifykey"})["value"]
        img_src = soup.find("img", {"alt": "此处为验证码"})["src"]
        while True:
            html = get(img_src, True)
            # 有时候获取不到图片，会显示文字，需要再刷新
            if not "javascript:history" in str(html):
                with open(verify_file, "wb") as f:
                    f.write(html)
                break
        print("请打开 %s ，识别验证码！" % verify_file)  # 必须显示，用print
        verifycode = input("请输入验证码：")
        print("继续执行")
        post_data["verifykey"] = verifykey
        post_data["verifycode"] = verifycode
        html = s.post(login_url, data=post_data)
    assert html.url.startswith(r"http://3g.renren.com/home"), "登录失败！请检查账号！"
    log("登录成功！")


def get_target_user_name(uid):
    """根据用户uid获取用户姓名"""
    html = get(user_url_pattern.format(uid))
    soup = BS(html, "lxml")
    tag = soup.find(name="div", class_="ssec")
    name = tag.find_next("b").string
    log("待抓取的用户的姓名为：%s" % str(name))
    return str(name)


def resolve_albums_queue(uid):
    """解析相册列表

    uid说明
        用户主页为：http://www.renren.com/123456789/profile
        网页中的123456789即为该用户的uid

    把结果存入Album对象，放入公共Queue albums_queue中
    """
    # 找出相册列表页
    html = get(user_url_pattern.format(uid))
    soup = BS(html, "lxml")
    albums_url = soup.find(name="a", text="相册")["href"]
    uid = re_uid_in_albums_url.findall(albums_url)[0]
    max_page = get_max_page(albums_url)
    # 遍历所有相册
    for i in range(max_page):
        # 组装网址
        url = albums_url_pattern.format(i,uid)
        resolve_albums_page(url)
    log("一共 %s 个相册" % albums_queue.qsize())


def get_max_page(url):
    """解析最大页数

    如：(第3/5页)
    返回类型为整数
    """
    soup = BS(get(url), "lxml")
    tmp = soup.find(name = "a", title = "末页")
    if not tmp:
        max_page = 0 # 只有一页
    else:
        tmp = tmp.find_next(name = "span", class_="gray")
        tmp = str(tmp.string)
        max_page = int(re_max_page.findall(tmp)[0])
    return max_page


def resolve_albums_page(url):
    """传入相册列表页，解析并存入Queue"""
    soup = BS(get(url), "lxml")
    tags = soup.find_all(name="a", class_="p")
    for tag in tags:
        album_url = tag["href"]
        tmp = tag.find_next(name="a", href=album_url)
        album_name = str(tmp.string)
        album_update_time = str(
            tmp.find_next(name="span", class_="ns").string)
        tmpStr = "相册名：%s\n%s" % (album_name, album_update_time)
        log(tmpStr)
        albums_queue.put(Album(album_name, album_url))


def resolve_photos_queue(album):
    """传入Album对象，解析出每张照片页面

    将结果存入Queue对象，每个元素为：(album_name, photo_page_url)
    """
    max_page = get_max_page(album.url) # album.url即照片列表第一页
    for i in range(max_page):
        url = photos_url_pattern.format(i, album.id, album.uid)
        resolve_photos_page(url, album.name)
    log("线程 %s 已解析相册：%s" % (threading.current_thread().name, album.name))


def resolve_photos_page(url, album_name):
    """传入照片列表页，解析出每张照片即photo对象"""
    soup = BS(get(url), "lxml")
    table = soup.find(name="table", class_="p")
    tags = table.find_all(name="a", href=re.compile(r"^http://"))
    for tag in tags:
        photo_page_url = tag["href"]
        photo_url = get_photo_url(photo_page_url)
        photos_queue.put(Photo(album_name, photo_url, photo_page_url))


def get_photo_url(photo_page_url):
    """解析并返回每张照片的url"""
    soup = BS(get(photo_page_url), "lxml")
    tag = soup.find(name="a", text="下载")
    photo_url = tag["href"]
    return photo_url


def down_photo(photo, filepath):
    """下载照片"""
    # 排除不能作为文件名的字符
    album_name = adjust_filename(photo.album_name)
    photo_name = adjust_filename(photo.name)
    # 保存照片的文件夹
    filepath = os.path.join(filepath, album_name)
    if not os.path.isdir(filepath):
        os.mkdir(filepath)
    # 照片
    file = os.path.join(filepath, photo_name)
    with open(file, "wb") as f:
        html = get(photo.url, True)
        f.write(html)
    log("已下载 %s\n%s" % (file, photo.url))


def adjust_filename(filename):
    """删掉不能出现在文件名中的字符"""
    return re_filename.sub("", filename)

# 秒-->时分秒


def trans_time(sec):
    hour = int(sec / 3600)
    sec = sec % 3600
    minute = int(sec / 60)
    sec = sec % 60
    return "%s小时 %s分 %s秒" % (hour, minute, sec)


class Album(object):

    """相册类"""
    count = 0
    re_uid = re.compile(r'owner=(\d+)&')
    re_album_id = re.compile(r'id=(\d+)&')

    def __init__(self, name, url):
        super(Album, self).__init__()
        self.name = name
        Album.count += 1
        self.uid = Album.re_uid.findall(url)[0]
        self.id = Album.re_album_id.findall(url)[0]
        # 即相册第一页，精简网址，删掉无用代码
        index = url.find(self.uid)
        self.url = url[:index+len(self.uid)]


class Photo(object):

    """照片类"""
    count = Counter()
    re_uid = re.compile(r'owner=(\d+)&')
    re_album_id = re.compile(r'albumid=(\d+)&')
    re_photo_id = re.compile(r'id=(\d+)&albumid')

    def __init__(self, album_name, photo_url, photo_page_url):
        super(Photo, self).__init__()
        self.album_name = album_name
        Photo.count[self.album_name] += 1
        self.url = photo_url  # 照片网址
        index = self.url.rfind(".")
        suffix = self.url[index:]
        self.name = str(Photo.count[self.album_name]) + suffix
        self.uid = Photo.re_uid.findall(photo_page_url)[0]
        self.album_id = Photo.re_album_id.findall(photo_page_url)[0]
        self.id = Photo.re_photo_id.findall(photo_page_url)[0]
        # 精简网址，删掉无用代码
        index = photo_page_url.find(self.uid)
        self.page_url = photo_page_url[:index+len(self.uid)]


if __name__ == '__main__':
    username = "xxx"
    password = "xxx"
    uid = "xxx"
    filepath = "F:\\"

    main(username, password, uid, filepath)
