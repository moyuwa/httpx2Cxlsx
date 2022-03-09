#!/usr/bin/env python3
# coding=utf-8
# python version 3.7 by 6time
# https://www.baidu.com/?id=1 AND 1=1 UNION ALL SELECT 1,NULL,'<script>alert(\"XSS\")</script>',table_name FROM information_schema.tables WHERE 2>1--/**/; EXEC xp_cmdshell('cat ../../../etc/passwd')#


# import identYwaf
# wwwsign = identYwaf.main("https://www.baidu.com")
# print(wwwsign)

import requests
import logging
import re

requests.packages.urllib3.disable_warnings()  # 关闭警告
logging.basicConfig(level=logging.INFO,  # 设置日志级别
                    format='%(asctime)s[%(levelname)s]%(module)s/%(funcName)s/%(lineno)d:%(message)s',
                    datefmt='%Y/%m/%d %X',
                    )

waf_probe_str = "/?id=1 AND 1=1 UNION ALL SELECT 1,NULL,'<script>alert(\"XSS\")</script>',table_name FROM information_schema.tables WHERE 2>1--/**/; EXEC xp_cmdshell('cat ../../../etc/passwd')"

CHECK_SPEED = 1
CHECK_HIGH = 2
WAF_YES = "WAF_YES"
WAF_NO = "WAF_NO"
WAF_ERROR = "WAF_ERROR"


class httpp_waf():
    def __init__(self, httpurl, json_finger):
        self.url = httpurl
        self.type = CHECK_SPEED
        self.has_waf = WAF_ERROR
        self.wafs_json_finger = json_finger
        self.waf_finger = ""
        self.req_ok = None
        self.req_waf = None

    def _httpwafget(self, httpurl):
        base_headers = {
            'Referer': httpurl,
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
        }
        try:
            req_ok = requests.get(
                url=httpurl,
                headers=base_headers,
                timeout=5,
                verify=False
            )
            logging.info("length:{} url:{}".format(len(req_ok.content), httpurl))
        except Exception as e:
            logging.error(e)
            req_ok = None
        req_waf = None
        if req_ok != None:
            try:
                req_waf = requests.get(
                    url=httpurl + waf_probe_str,
                    headers=base_headers,
                    timeout=5,
                    verify=False
                )
                logging.info("length:{} url:{}".format(len(req_waf.content), httpurl + waf_probe_str))
            except Exception as e:
                logging.error(e)
                req_waf = None
        return req_ok, req_waf

    def checkWAF(self):
        self.req_ok, self.req_waf = self._httpwafget(self.url)
        if self.req_ok == None or self.req_waf == None:  # 请求出错
            self.has_waf = WAF_ERROR
            return WAF_ERROR
        if self.type == CHECK_SPEED:
            if (len(self.req_ok.content) - len(self.req_waf.content)) > (len(self.req_ok.content) / 2):
                self.has_waf = WAF_YES
                return WAF_YES
        if self.type == CHECK_HIGH:
            text = str(self.req_waf.headers) + self.req_waf.text
            for waf in self.wafs_json_finger["wafs"]:
                waf = self.wafs_json_finger["wafs"][waf]
                if waf["regex"]:
                    if re.search(waf["regex"], text) != None:
                        self.waf_finger = waf["name"]
                        self.has_waf = WAF_YES
                        return WAF_YES
        self.has_waf = WAF_NO
        return WAF_NO


if __name__ == "__main__":
    httpurl = "https://www.qq.com"
