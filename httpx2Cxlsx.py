#!/usr/bin/env python3
# coding=utf-8
# python version 3.7 by 6time
# 将 httpx 输出的文件 转为 表格带颜色文件
# ./httpx.exe -l domains.txt -sc -td -cl -method -server -title -cdn -probe -t 100 -o output.txt
import os, ctypes
from openpyxl.styles import Font
from openpyxl import Workbook
import logging  # 引入logging模块

logging.basicConfig(level=logging.INFO,  # 设置日志级别
                    format='%(asctime)s[%(levelname)s]:%(message)s',
                    datefmt='%Y/%m/%d %X',
                    )
import argparse

parser = argparse.ArgumentParser(description="""
python version 3.7 by 6time
将httpx带颜色的输出转为xlsx表格（httpx不要使用-nc参数）
httpx.exe -l domains.txt [-sc -td -cl -method -server -title -cdn -probe -t 100] -o output.txt
httx2Cxlsx.py -f output.txt -o output.xlsx -cdn 1 -waf 1
""")
parser.add_argument('-f', '--file', type=str, default=None, help='httpx输出保存的txt文件')
parser.add_argument('-o', '--outfile', type=str, default=None, help='xlsx表格文件输出名称')
parser.add_argument('-cdn', '--checkcdn', type=str, default=None, help='对httpx输出结果使用cdn增强检查功能')
parser.add_argument('-waf', '--checkwaf', type=str, default=None, help='对httpx输出结果使用waf增强检查功能')
args = parser.parse_args()

colordict = {
    # Font(name=字体名称,size=字体大小,bold=是否加粗,italic=是否斜体,color=字体颜色)
    "31m": Font(name="宋体", size=11, bold=False, italic=False, color="FF0000"),  # 红 # RGB 的 16 进制表示
    "32m": Font(name="宋体", size=11, bold=False, italic=False, color="00ff00"),  # 绿
    "33m": Font(name="宋体", size=11, bold=False, italic=False, color="ffff00"),  # 黄
    # "34m": Font(name="宋体", size=11, bold=False, italic=False, color="FF0000"),
    "35m": Font(name="宋体", size=11, bold=False, italic=False, color="9900ff"),  # 紫
    "36m": Font(name="宋体", size=11, bold=False, italic=False, color="0000FF"),  # 蓝
    "default": Font(name="宋体", size=11, bold=False, italic=False, color="000000"),  # 黑

}


# 处理httpx输出字符串
def readhttpxfile(txtpath):
    xlsxdatas = []
    with open(txtpath, "rb") as httpxf:  # ,encoding="utf-8"
        for line in httpxf.readlines():
            # 处理不可见字符
            line = line.replace(b"\x1b", b"")
            # datas = str(line, encoding="utf-8").rstrip().replace("[0m", "").replace("]", "").split(" [")
            datas = []
            for l in line.replace(b"[0m", b"").replace(b"]", b"").split(b" ["):
                try:
                    datas.append(str(l, encoding="utf-8").rstrip())
                except Exception as e:
                    try:
                        datas.append(str(l, encoding="gb2312").rstrip())
                    except Exception as e:
                        print(e, l)
                        datas.append("******")
            # print(datas)
            # return xlsxdatas
            # 获取各字段颜色
            color_datas = []
            for i in range(len(datas)):
                notfind = True
                for m1 in colordict.keys():
                    if m1 in datas[i]:
                        d = datas[i].replace(m1, "$$$").split("$$$")[-1]
                        color_datas.append((d, m1))
                        notfind = False
                if notfind:
                    color_datas.append((datas[i], "default"))  # 默认黑色
            xlsxdatas.append(color_datas)
            # print(color_datas)
    return xlsxdatas


# 写入到xlsx
def outxlsx(xlsxpath, xlsxdatas=[]):
    wb = Workbook()
    # ws = wb.active
    sheet = wb['Sheet']  # 创建表格文件
    sheet.title = 'httpx'
    sheet.append(["url", "存活", "httpx", "httpx", "httpx",
                  "httpx", "httpx", "httpx", "httpx", "httpx",
                  "httpx", "httpx", "httpx", "httpx", "httpx"])  # 添加首行
    y = 2
    for data in xlsxdatas:
        for x in range(len(data)):
            # sheet.font = colordict[data[x][1]]
            sheet.cell(row=y, column=x + 1, value=data[x][0]).font = colordict[data[x][1]]
            # sheet.font = colordict[data[x][1]]
        y += 1
    wb.save(filename=xlsxpath)


from urllib.parse import urlparse
import probecdn
import probewaf
import re, json
from concurrent.futures import ThreadPoolExecutor, wait, as_completed


def checkcdn(data):
    if str(data[1][0]).find("FAILED") != -1:
        data.insert(2, ("", "default"))
        return data
    o = urlparse(data[0][0])
    if re.search("((?:[0-9]{1,3}\.){3}[0-9]{1,3})", o.hostname):  # 传入ip
        data.insert(2, ("", "default"))
        return data
    else:
        cdn = probecdn.httpp_cdn("")
        cdn.domain = o.hostname
        cdn.checkCDN()
        data.insert(2, (cdn.has_cdn, "default"))
    return data


with open("data.json", "r", encoding="utf-8") as f:
    wafs_json_finger = json.load(f)


def checkwaf(data):
    if str(data[1][0]).find("FAILED") != -1:
        data.insert(2, ("", "default"))
        return data
    waf = probewaf.httpp_waf("", wafs_json_finger)
    waf.url = data[0][0]
    waf.checkWAF()
    data.insert(2, (waf.has_waf, "default"))
    return data


def main():
    txtpath = args.file
    xlsxpath = args.outfile
    logging.info("===========开始转换==========")
    xlsxdatas = readhttpxfile(txtpath)
    logging.info("===========转换完成，开始探测==========")
    _www_th_pool = ThreadPoolExecutor(max_workers=16)
    if args.checkcdn:
        logging.info("===========探测CDN==========")
        all_task = [_www_th_pool.submit(checkcdn, data) for data in xlsxdatas]
        xlsxdatas = []
        for future in as_completed(all_task):
            if future.result():
                xlsxdatas.append(future.result())
    if args.checkwaf:
        logging.info("===========探测WAF==========")
        all_task = [_www_th_pool.submit(checkwaf, data) for data in xlsxdatas]
        xlsxdatas = []
        for future in as_completed(all_task):
            if future.result():
                xlsxdatas.append(future.result())
    outxlsx(xlsxpath, xlsxdatas)
    logging.info("===========执行结束==========")


if __name__ == '__main__':
    if args.file == None or args.outfile == None:
        print("参数错误请查看帮助 python httpx2Cxlsx.py -h")
        exit(-1)
    main()
