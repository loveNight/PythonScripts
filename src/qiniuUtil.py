#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: LoveNight
# @Date:   2015-11-16 18:17:17
# @Last Modified by:   LoveNight
# @Last Modified time: 2015-11-16 19:50:15

import qiniu
import urllib


__author__ = "loveNight"


class Qiniu(object):

    """七牛上传与下载的工具类

    需要七牛的Python SDK
    pip install qiniu
    SDK详细用法见　http://developer.qiniu.com/docs/v6/sdk/python-sdk.html
    """
    SUCCESS_INFO = "上传成功！"

    # 上传空间的域名，需要自己去后台获取
    bucket_url = {
        自己去后台查
    }

    def __init__(self, accessKey, secretkey):
        self.accessKey = accessKey
        self.secretkey = secretkey
        self._q = qiniu.Auth(self.accessKey, self.secretkey)

    def upload_file(self, bucket_name, up_filename, file_path):
        """上传文件

        Args:
            bucket_name: 上传空间的名字
            up_filename: 上传后的文件名
            file_path:   本地文件的路径
        Returns:
            成功提示或错误信息
        """
        token = self._q.upload_token(bucket_name)
        ret, info = qiniu.put_file(token, up_filename, file_path)
        if ret is not None:
            url = self.get_file_url(bucket_name, up_filename)
            return Qiniu.SUCCESS_INFO + "\n文件地址\n" + url
        return info

    def get_file_url(self, bucket_name, up_filename):
        if not bucket_name in Qiniu.bucket_url.keys():
            raise AttributeError("空间名不正确！")
        url_prefix = Qiniu.bucket_url[bucket_name]
        url = url_prefix + urllib.parse.quote(up_filename)
        return url


if __name__ == '__main__':
    accessKey = 自己去后台查
    secretkey = 自己去后台查
    q = Qiniu(accessKey, secretkey)
    # print(q.upload_data("blog", "test/string.txt", "HelloWorld!"))
    info = q.upload_file(
        "blog", "img/编程/hexo/Hexo NexT主题个性化设置/巨慢的打开速度.png", r"d:\backup\140591\桌面\首页图片\巨慢的打开速度.png")
    print(info)
