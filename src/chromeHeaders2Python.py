#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: LostInNight
# @Date:   2015-11-03 20:02:27
# @Last Modified by:   LostInNight
# @Last Modified time: 2015-11-03 20:07:56


# Chrome 截获的Headers转化为Python可用的dict，输出未排版

s = '''Accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Encoding:gzip, deflate, sdch
Accept-Language:zh-CN,zh;q=0.8
Connection:keep-alive
Cookie:x-wl-uid=16g0A+YFYxJfKEtYdu3jnjT5fyfFfYsVwN90XyuIvu1ooEwLD0rk+ETnyp1GE4/LFXUyqbPPCNSE=; session-token=dL8l1xW56RLj3F3P2p6szy6b7MH7R3o1EosxprqS0ci8JaUN9kJ212ybOIEXgV/Iif/rN2LFToQlyJyV/Q69NLnbRfvI4qArBPLDRJoXb+tjUsrF+z7yXznFtEFiQ52O2lc2k1tOTsKWX4u1h7N5W/O1Y2jFF0XMB2Somg9zeSPrTPTJyVBoWl3M+M5lW7S3vX1BueyzUJKPorQ+z3lXsQ98os2NrZwhLpndF14RkKNbuRPkKluj+Q==; session-id-time=2082729601l; session-id=476-5989535-3128668; csm-hit=0GASN13S1NXJ6XZDVCSF+sa-1K96W079F5G590GEQAK7-1FZS7C1YHF9SGAH3Q9W4|1446303517108; ubid-acbcn=475-2664832-5552339
Host:www.amazon.cn
Upgrade-Insecure-Requests:1
User-Agent:Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.71 Safari/537.36
'''
s = s.strip().split('\n')
s = {x.split(':')[0] : x.split(':')[1] for x in s}
print(s)
