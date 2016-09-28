#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: LoveNight
# @Date:   2015-11-23 17:56:34
# @Last Modified by:   LoveNight
# @Last Modified time: 2015-11-25 13:23:07

import configparser
import sys
import os
import requests
import json
import re
import base64
from datetime import datetime
import time


class WeiboUtil(object):

    """新浪微博脚本

    需要把App Key和Access Token写入同目录下的config.ini。格式如下：
    [Account]
    appKey = XXXXXXXXXXX
    accessToken = XXXXXXXXXXXXXXX
    cookie = 没有可以不填

    其中：
    app_key：登录后在「我的应用」里可以找到
    Access Token 登录后访问：http://open.weibo.com/tools/console?uri=statuses/update&httpmethod=POST&key1=status&value1=%E5%BE%AE%E5%8D%9A%E6%9D%A5%E8%87%AAAPI%E6%B5%8B%E8%AF%95%E5%B7%A5%E5%85%B7
    """
    configFile = "config.ini"
    headers = {
        "accept-encoding": "gzip, deflate, sdch",
        "Upgrade-Insecure-Requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.71 Safari/537.36",
    }
    postData = {
        "entry": "sso",
        "gateway": "1",
        "from": "null",
        "savestate": "30",
        "useticket": "0",
        "pagerefer": "",
        "vsnf": "1",
        "su": "base64编码后的用户名",
        "service": "sso",
        "sp": "密码明文",
        "sr": "1440*900",
        "encoding": "UTF-8",
        "cdult": "3",
        "domain": "sina.com.cn",
        "prelt": "0",
        "returntype": "TEXT",
    }

    # GET 请求
    loginURL = r'https://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.15)'
    timeLineURL = r'https://api.weibo.com/2/statuses/friends_timeline.json?&since_id={since_id}&max_id={max_id}&count={count}&page={page}&feature={feature}'
    friendsURL = r'https://api.weibo.com/2/friendships/friends.json?&uid={uid}&count={count}&cursor={cursor}&trim_status={trim_status}'
    friendsIdsUrl = r'https://api.weibo.com/2/friendships/friends/ids.json?&uid={uid}&count={count}&cursor={cursor}'
    currentUserUidUrl = r'https://api.weibo.com/2/account/get_uid.json?'
    bilateralTimelineURL = r'https://api.weibo.com/2/statuses/bilateral_timeline.json?&since_id={since_id}&max_id={max_id}&count={count}&page={page}&feature={feature}'

    # POST请求
    updateURL = r'https://api.weibo.com/2/statuses/update.json'
    uploadURL = r'https://upload.api.weibo.com/2/statuses/upload.json'
    commentURL = r'https://api.weibo.com/2/comments/create.json'

    def __init__(self, auth = "access_token"):
        config = configparser.ConfigParser()
        config.read(os.path.join(sys.path[0], WeiboUtil.configFile))
        self.app_key = config.get("Account", "appKey")
        self.access_token = config.get("Account", "accessToken")
        self.cookie = config.get("Account", "cookie")
        self.auth = "&access_token=" + self.access_token
        self.timeline_since_id = 0 # 标识微博TimeLine读取到了哪一条
        self.bilateral_timeline_since_id = 0
        self.session = requests.Session()
        if self.cookie:
            WeiboUtil.headers["cookie"] = cookie
        self.session.headers = WeiboUtil.headers

    def login(self, username, password):
        """登录微博"""
        self.auth = "&source=" + self.app_key
        self.username = username
        self.password = password
        self.username = base64.b64encode(
            self.username.encode('utf-8')).decode('utf-8')
        WeiboUtil.postData["su"] = self.username
        WeiboUtil.postData["sp"] = self.password
        res = self.session.post(WeiboUtil.loginURL, data=WeiboUtil.postData)
        jsonStr = res.content.decode('gbk')
        info = json.loads(jsonStr)
        if info["retcode"] == "0":
            print("登录成功")
            # 把cookies添加到headers中，必须写这一步，否则后面调用API失败
            cookies = self.session.cookies.get_dict()
            cookies = [key + "=" + value for key, value in cookies.items()]
            cookies = "; ".join(cookies)
            self.session.headers["cookie"] = cookies
        else:
            print("登录失败，原因： %s" % info["reason"])

    # 一般用不着
    def _getCurrentUID(self):
        """获取当前登录用户的UID

        UID API：http://open.weibo.com/wiki/2/account/get_uid
        """
        url = WeiboUtil.currentUserUidUrl.format(access_token=self.access_token) + self.auth
        jsonStr = self.session.get(url).text
        data = self._getJson(url)
        self.uid = data["uid"]

    def _getJson(self, url, data=None, files = None, post=False):
        """发送HTTP请求并将返回的JSON字符串格式化"""
        if post:
            jsonStr = self.session.post(url, data=data, files=files).text
        else:
            jsonStr = self.session.get(url).text
        return json.loads(jsonStr)

    def update(self, text):
        """发微博，pic为图片网址或本地绝对路径

        update API: http://open.weibo.com/wiki/2/statuses/update
        upload API: http://open.weibo.com/wiki/2/statuses/upload
        source string        采用OAuth授权方式不需要此参数，其他授权方式为必填参数，数值为应用的AppKey。
        access_token string  采用OAuth授权方式为必填参数，其他授权方式不需要此参数，OAuth授权后获得。
        status string        必填。要发布的微博文本内容，必须做URLencode，内容不超过140个汉字。
        visible int          微博的可见性，0：所有人能看，1：仅自己可见，2：密友可见，3：指定分组可见，默认为0。
        list_id string       微博的保护投递指定分组ID，只有当visible参数为3时生效且必选。
        lat float            纬度，有效范围：-90.0到+90.0，+表示北纬，默认为0.0。
        long float           经度，有效范围：-180.0到+180.0，+表示东经，默认为0.0。
        annotations string   元数据，主要是为了方便第三方应用记录一些适合于自己使用的信息，每条微博可以包含一个或者多个元数据，必须以json字串的形式提交，字串长度不超过512个字符，具体内容可以自定。
        rip string           开发者上报的操作用户真实IP，形如：211.156.0.1。

        upload API 多一个字段：pic binary  要上传的图片，仅支持JPEG、GIF、PNG格式，图片大小小于5M。
        """
        postData = {
            "access_token":self.access_token,
            "status":text,
        }
        url = WeiboUtil.updateURL
        data = self._getJson(url, data=postData, post = True)
        status = Status()
        status.fromDict(data)
        return status


    def comment(self, text, weiboID, comment_ori=0):
        """评论微博，每小时只能发十五条

        comment API : http://open.weibo.com/wiki/2/comments/create
        comment string   必填。评论内容，必须做URLencode，内容不超过140个汉字。
        id int64         必填需要评论的微博ID。
        comment_ori int  当评论转发微博时，是否评论给原微博，0：否、1：是，默认为0。
        rip string       开发者上报的操作用户真实IP，形如：211.156.0.1。
        """
        postData = {
            "access_token":self.access_token,
            "comment":text,
            "id":weiboID
        }
        data = self._getJson(WeiboUtil.commentURL, data=postData, post=True)
        print(data)
        print("="*50)
        # comment = Comment()
        # comment.fromDict(data)
        # return comment


    def getTimeline(self, max_id=0, count=100, page=1, feature=0):
        """读取时间线上的微博

        TimeLine API：http://open.weibo.com/wiki/2/statuses/friends_timeline
        since_id 则返回ID比since_id大的微博（即比since_id时间晚的微博），默认为0。
        max_id 则返回ID小于或等于max_id的微博，默认为0。
        count 单页返回的记录条数，最大不超过100，默认为20。
        page 返回结果的页码，默认为1。
        feature 过滤类型ID，0：全部、1：原创、2：图片、3：视频、4：音乐，默认为0。
        """
        url = WeiboUtil.timeLineURL.format(app_key=self.app_key, since_id=self.timeline_since_id, max_id=max_id, count=count, page=page, feature=feature) + self.auth
        # print(url)
        weiboInfo = self._getJson(url)
        self.timeline_since_id = weiboInfo["since_id"]
        max_id = weiboInfo["max_id"]
        weiboPosts = weiboInfo["statuses"]
        # print(len(statuses))
        statuses = []
        for post in weiboPosts:
            status = Status()
            status.fromDict(post)
            statuses.append(status)
        return statuses


    def getBilateralTimeline(self, max_id=0, count=100, page=1, feature=0):
        """获取互相关注好友的时间线

        bilateral_timeline API: http://open.weibo.com/wiki/2/statuses/bilateral_timeline
        since_id int64   若指定此参数，则返回ID比since_id大的微博（即比since_id时间晚的微博），默认为0。
        max_id int64     若指定此参数，则返回ID小于或等于max_id的微博，默认为0。
        count int        单页返回的记录条数，最大不超过100，默认为20。
        page int         返回结果的页码，默认为1。
        feature int      过滤类型ID，0：全部、1：原创、2：图片、3：视频、4：音乐，默认为0。
        """
        url = WeiboUtil.bilateralTimelineURL.format(app_key=self.app_key, since_id=self.bilateral_timeline_since_id, max_id=max_id, count=count, page=page, feature=feature) + self.auth
        # print(url)
        data = self._getJson(url)
        try:
            weiboPosts = data["statuses"]
            self.bilateral_timeline_since_id = data["since_id"]
            statuses = []
            for post in weiboPosts:
                status = Status()
                status.fromDict(post)
                statuses.append(status)
            return statuses
        except Exception as e:
            msg = str(e)+"\n"+str(data)
            return msg


    def printLimit(self):
        url = r'https://api.weibo.com/2/account/rate_limit_status.json?'+self.auth
        data = self._getJson(url)
        commit_limit_remaining=data["api_rate_limits"][1]["remaining_hits"]
        print("剩余评论数", commit_limit_remaining)



class Status(object):
    """单条微博类"""

    visible_type = {
        0:"普通微博", 1:"私密微博", 3:"指定分组微博", 4:"密友微博"
    }
    def __init__(self):
        pass

    def fromJsonStr(self, jsonStr):
        """从字符串中提取信息"""
        data = json.loads(jsonStr)
        self.fromDict(data)

    def fromDict(self, data):
        self.created_at = data["created_at"]
        self.id = data["id"]
        self.text = data["text"] # 微博内容
        self.source = data["source"]
        self.favorited = data["favorited"]
        self.truncated = data["truncated"]
        userJson = data["user"]
        self.user = User()
        self.user.fromDict(userJson) # 作者
        self.reposts_count = data["reposts_count"] # 转发数
        self.comments_count = data["comments_count"]
        self.attitudes_count = data["attitudes_count"] # 表态数
        self.visible = data["visible"]["type"] # 可见性
        # print(self.visible)
        self.visible = Status.visible_type.get(self.visible)


class User(object):
    """微博用户类

    Weibo User API:http://open.weibo.com/wiki/%E5%B8%B8%E8%A7%81%E8%BF%94%E5%9B%9E%E5%AF%B9%E8%B1%A1%E6%95%B0%E6%8D%AE%E7%BB%93%E6%9E%84#.E7.94.A8.E6.88.B7.EF.BC.88user.EF.BC.89
    """
    def __init__(self):
        pass

    def fromJsonStr(self, jsonStr):
        """从字符串中提取信息"""
        data = json.loads(jsonStr)
        self.fromDict(data)

    def fromDict(self, data):
        self.uid = data["id"]
        self.screen_name = data["screen_name"]
        self.name = data["name"]
        self.provinceID = data["province"]
        self.cityID = data["city"]
        self.location = data["location"]
        self.description = data["description"]
        self.blogURL = data["url"]
        self.profile_image_url = data["profile_image_url"] # 头像，50 * 50
        self.avatar_large = data["avatar_large"] # 头像，180 * 180
        self.avatar_hd = data["avatar_hd"] # 头像，原图
        self.gender = data["gender"] # 性别，m：男、f：女、n：未知
        self.followers_count = data["followers_count"]
        self.friends_count = data["friends_count"] # 关注数
        self.statuses_count = data["statuses_count"] # 微博数
        self.favourites_count = data["favourites_count"]
        self.created_at = data["created_at"]
        self.allow_all_act_msg = data["allow_all_act_msg"] # 是否允许所有人给我发私信
        self.allow_all_comment = data["allow_all_comment"] # 是否允许所有人评论微博
        self.verified = data["verified"] # 是否大V
        self.following = data["following"] # 当前登录用户是否关注对方
        self.follow_me = data["follow_me"] # 是否关注当前登录用户
        self.online_status = data["online_status"] # 在线状态
        self.bi_followers_count = data["bi_followers_count"] # 互粉数

class Comment(object):
    """单条评论的类"""
    def __init__(self):
        pass

    def fromJsonStr(self, jsonStr):
        data = json.loads(jsonStr)
        self.fromDict(data)

    def fromDict(self, data):
        self.created_at = data["created_at"]
        self.id = data["id"]
        self.text = data["text"]
        self.source = data["source"]
        self.mid = data["mid"]
        self.status = Status()
        self.status.fromDict(data["status"])
        self.user = User()
        self.user.fromDict(data["user"])


if __name__ == '__main__':
    # 使用前先根据WeiboUtil的说明文字配置好config.ini

    u = WeiboUtil()
    # print(u.access_token)
    # u.printLimit()

    # 默认使用access_token验证，不需要用户名密码。

    # 如果access_token验证失败，改用app_key，此时需要用户名密码登陆
    # u.login("用户名", "密码")

    # # 读取Timeline上的一百条最新微博
    # statuses = u.getTimeline()

    # # 读取互相关注好友的最新微博，最多一百条
    # statuses = u.getBilateralTimeline()
    # print(statuses)
    # for status in statuses:
    #     print(status.user.name) # 作者
    #     print(status.text) # 微博内容，更多属性请查看Status和User类
    #     print("=" * 50)

    # # ---------------评论其中的第一条微博------------------------
    # weiboID = statuses[0].id
    # print(weiboID)
    # print("评论的微博：", statuses[0].text)
    # print("用户:", statuses[0].user.name)
    # for _ in range(100):
    #     comment = u.comment("小金微博机器人测试 " + str(_) + " " + str(datetime.now()), weiboID)


    # # 发一条新的纯文本微博
    # text = "小金微博机器人测试"
    # status = u.update(text) # 返回单条微博对象
    # print(status)

    # 发一条带图片的微博，还没调试成功
    # 相关资料http://hbprotoss.github.io/posts/multipartform-datade-shi-xian.html


