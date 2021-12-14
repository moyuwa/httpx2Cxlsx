#!/usr/bin/env python3
# coding=utf-8
# python version 3.7 by 6time
# 将 httpx 输出的文件 转为 表格带颜色文件
# ./httpx.exe -l domains.txt -sc -td -cl -method -server -title -cdn -probe -t 100 -o output.txt


import os, ctypes
from openpyxl.styles import Font
from openpyxl import Workbook

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
# colordict.values()

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
            color_datas = {}
            for i in range(len(datas)):
                notfind = True
                for m1 in colordict.keys():
                    if m1 in datas[i]:
                        d = datas[i].replace(m1, "$$$").split("$$$")[-1]
                        color_datas[i] = (d, m1)
                        notfind = False
                if notfind:
                    color_datas[i] = (datas[i], "default")  # 默认黑色
            xlsxdatas.append(color_datas)
            # print(color_datas)
    return xlsxdatas


# 写入到xlsx
def outxlsx(xlsxpath, xlsxdatas=[]):
    wb = Workbook()
    # ws = wb.active
    sheet = wb['Sheet']  # 创建表格文件
    sheet.title = 'httpx'
    y = 2
    for data in xlsxdatas:
        for x in range(len(data)):
            # sheet.font = colordict[data[x][1]]
            sheet.cell(row=y, column=x+1, value=data[x][0]).font = colordict[data[x][1]]
            # sheet.font = colordict[data[x][1]]
        y += 1
    wb.save(filename=xlsxpath)


if __name__ == '__main__':
    print("""=========httpx out 2 xlsx=========
    httpx.exe -l domains.txt [-sc -td -cl -method -server -title -cdn -probe -t 100] -o output.txt""")
    txtpath = "output.txt"
    xlsxdatas = readhttpxfile(txtpath)
    xlsxpath = "httpx.xlsx"
    outxlsx(xlsxpath, xlsxdatas)
