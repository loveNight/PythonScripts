#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: LoveNight
# @Date:   2016-01-29 16:42:01
# @Last Modified by:   LoveNight
# @Last Modified time: 2016-09-28 18:15:21

"""
用于处理VBA程序下载下来的文本数据

将文件拖放到本脚本上即可
"""




import sys


def replaceFutID(file):
    '''
    将合约第二列的 棉花#CF603 替换成 1603
    规则：后三位不变，其他全换成 1
    列与列之间用|间隔
    '''
    with open(file, 'r', encoding="gbk") as f:
        content = f.readlines()
        new = []
        # print(content)
        for line in content:
            start = line.find("|") + 1  # 第二列起始
            end = line.find("|", start) - 1  # 第二列结尾
            new.append(line.replace(line[start:(end - 2)], "1"))
    with open(file, 'w', encoding='gbk') as f:
        f.writelines(new)


if __name__ == '__main__':

    if len(sys.argv) == 1:
        print("请将文件拖曳到本脚本！")
        sys.exit(0)
    files = sys.argv[1:]

    for file in files:
        replaceFutID(file)
