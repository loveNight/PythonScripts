#! python3
# -*- coding: utf-8 -*-
# @Author: LoveNight
# @Date:   2016-09-26 17:24:42
# @Last Modified by:   LoveNight
# @Last Modified time: 2016-09-27 17:25:18


"""
由于用到了develop链接，只能在公司使用

用法：双击本脚本

效果：理缓存并提取每日指数，结果如下：

9月26日大宗商品价格指数BPI为744点，与昨日持平
9月26日能源指数为607点，较昨日上升了1点
9月26日化工指数为684点，较昨日上升了5点
9月26日建材指数为775点，与昨日持平
9月26日有色指数为749点，较昨日下降了2点
9月26日农副指数为944点，较昨日下降了2点
9月26日橡塑指数为691点，与昨日持平
9月26日钢铁指数为695点，较昨日上升了2点
9月26日纺织指数为815点，较昨日上升了1点
"""





import urllib.request
import re
import time
import sys
import os
import subprocess


save_file = os.path.join(sys.path[0], "今日指数.txt")
re_get_cindex = re.compile(
    r'class="nd-p">&nbsp;&nbsp;&nbsp;&nbsp;(.*?)，较周期')
url = [r"http://www.100ppi.com/cindex/",
       r"http://www.100ppi.com/cindex/nyzs.html",
       r"http://www.100ppi.com/cindex/hgzs.html",
       r"http://www.100ppi.com/cindex/jczs.html",
       r"http://www.100ppi.com/cindex/yszs.html",
       r"http://www.100ppi.com/cindex/nfzs.html",
       r"http://www.100ppi.com/cindex/xszs.html",
       r"http://www.100ppi.com/cindex/gtzs.html",
       r"http://www.100ppi.com/cindex/fzzs.html"]
purge_url = r"http://develop.100ppi.com/admin/squidclient.pl"

delay = 5

# 清理缓存，出错就重试……


def purge(url):
    data = {
        "f": "purge",
        "url": url,
        "site": 1,
        "submit_regional": "更新"
    }
    data = urllib.parse.urlencode(data).encode("gb2312")
    req = urllib.request.Request(purge_url)
    try:
        res = urllib.request.urlopen(req, data=data)
        html = res.read().decode("gb2312")
        if "Successful purge" in html:
            return "Successs"
        elif "not found on this server" in html:
            return "本页面没有新的内容"
    except:
        print("Fail！等待" + str(delay) + "秒后重试...")
        time.sleep(delay)
        purge(url)

# 读取网页，出错就重试


def get_html(url):
    try:
        return urllib.request.urlopen(url).read().decode("utf-8")
    except Exception as e:
        print("Fail！等待" + str(delay) + "秒后重试...")
        time.sleep(delay)
        return get_html(url)


def main():
    # 如果结果文件已存在，则删除
    if os.path.exists(save_file):
        os.remove(save_file)

    # 先清理缓存
    for x in url:
        print("正在清理缓存： " + x)
        result = purge(x)
        print(result)

    print("缓存清理结束，开始提取指数...")

    # 再依次提取字符串
    result = ""
    for x in url:
        print("正在提取指数：" + x)
        data = get_html(x)
        # print(re_get_cindex.findall(data))
        result += re_get_cindex.findall(data)[0] + "\n"
        print("Success")

    # 去除无关代码
    result = result.replace(r'<span style="color:red">', '')
    result = result.replace(r'<span style="color:green">', '')
    result = result.replace(r'</span>', '')

    # print(result)
    with open(save_file, "w") as f:
        f.write(result)
    subprocess.call(save_file, shell=True)  # 打开文件

if __name__ == '__main__':
    main()
