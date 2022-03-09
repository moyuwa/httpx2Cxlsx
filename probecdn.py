#!/usr/bin/env python3
# coding=utf-8
# python version 3.7 by 6time
# https://blog.51cto.com/u_13398760/2491534
# https://blog.csdn.net/qq_44009891/article/details/106851001
# https://dnspython.readthedocs.io/en/stable/name.html


import dns.resolver
from concurrent.futures import ThreadPoolExecutor, wait, as_completed
import re
import logging

logging.basicConfig(level=logging.INFO,  # 设置日志级别
                    format='%(asctime)s[%(levelname)s]%(module)s/%(funcName)s/%(lineno)d:%(message)s',
                    datefmt='%Y/%m/%d %X',
                    )

nameserver_zh = ["58.132.8.1",  # 北京市 教育网DNS服务器
                 "114.114.114.114",  # 江苏省南京市 南京信风网络科技有限公司GreatbitDNS服务器
                 "202.98.192.67",  # 贵州电信 DNS
                 ]
nameserver_en = ["8.8.8.8",  # 美国 加利福尼亚州圣克拉拉县山景市谷歌公司DNS服务器
                 "77.88.8.8",  # 俄国 搜索引擎 Yandex 服务器
                 "61.47.33.9",  # 新加坡 Pacific互联网泰国有限公司新加坡节点DNS服务器
                 ]
nameserver_all = ["1.1.1.1",  # 美国 APNIC&CloudFlare公共DNS服务器
                  "8.8.8.8",  # 美国 加利福尼亚州圣克拉拉县山景市谷歌公司DNS服务器
                  "77.88.8.8",  # 俄国 搜索引擎 Yandex 服务器

                  "61.47.33.9",  # 新加坡 Pacific互联网泰国有限公司新加坡节点DNS服务器

                  "202.14.67.4",  # 香港 亚太环通(Pacnet)有限公司DNS服务器
                  "61.10.1.130",  # 香港 CableTVDNS服务器

                  "118.118.118.118",  # 上海市 电信DNS服务器(全国通用)
                  "202.98.192.67",  # 贵州电信 DNS

                  "58.132.8.1",  # 北京市 教育网DNS服务器
                  "114.114.114.114",  # 江苏省南京市 南京信风网络科技有限公司GreatbitDNS服务器
                  "223.5.5.5",  # 浙江省杭州市 阿里巴巴anycast公共DNS
                  ]

CHECK_SPEED = 1
CHECK_HIGH = 2
CDN_YES = "CDN_YES"
CDN_NO = "CDN_NO"
CDN_ERROR = "CDN_ERROR"


class httpp_cdn():
    def __init__(self, domain):
        self.domain = domain
        self.ips = []
        self.has_cdn = CDN_ERROR
        self.type = CHECK_SPEED

    def _nslookup(self, domain, nameserver):
        my_resolver = dns.resolver.Resolver()
        my_resolver.nameservers = [nameserver]
        try:
            A = my_resolver.resolve(domain, dns.rdatatype.A)
            A = my_resolver.resolve(domain, lifetime=5)  # 可自定义超时
            # for i in A.response.answer:
            #     print(i.to_text())
            pattern = re.compile('((?:[0-9]{1,3}\.){3}[0-9]{1,3})')
            # print(re.search(pattern, str(A.rrset)))
            result = re.search(pattern, str(A.rrset))
            if result:
                return result.group(1)
        except Exception as e:
            logging.warning(e)
        return False

    def _getips(self, domain, nameserver_list):
        _www_th_pool = ThreadPoolExecutor(max_workers=3)  # 创建线程池
        all_task = [_www_th_pool.submit(self._nslookup, domain, ns) for ns in nameserver_list]

        ips = []
        for future in as_completed(all_task):
            if future.result():
                ips.append(future.result())

        # _www_th_pool.shutdown()
        return ips

    def _checkips(self, ips):
        if len(ips) == 0:  # 解析失败 域名不存在或失效
            logging.error(self.domain)
            return CDN_ERROR
        if len(ips) == 1:  # 只解析出1个认为没有cdn
            logging.warning(ips)
            return CDN_NO
        if len(list(set(ips))) != 1:  # 去重后ip数大于1则存在cdn
            return CDN_YES
        return CDN_NO

    def checkCDN(self):
        logging.info("checkCDN {}".format(self.domain))
        if self.type == CHECK_SPEED:
            self.ips = self._getips(self.domain, nameserver_zh)
        if self.type == CHECK_HIGH:
            self.ips = self._getips(self.domain, nameserver_all)
        # 针对国外IP优化 暂未实现
        # if self.type == :
        #     self.ips = self.getips(self.domain, nameserver_en)
        logging.info(str(self.ips))
        self.has_cdn = self._checkips(self.ips)
        return self.has_cdn


if __name__ == "__main__":
    domain = "www.baidu.com"
