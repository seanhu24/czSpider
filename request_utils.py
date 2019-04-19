# -*- coding: utf-8 -*-

import requests
from requests import RequestException
import time
from logging.config import fileConfig
import logging

fileConfig('logging_config.ini')
logger = logging.getLogger('sLogger')


def get_one_url(url):
    # logger.info('爬取url:' + url)
    retry = 3
    success = False
    while not success:
        try:
            resp = requests.get(url)
            success = True
            if resp.status_code == 200:
                resp.encoding = 'utf-8'  # 解决中文问题
                return resp.text
            return None
        except RequestException:
            logger.error('请求索引页出错')
            for i in range(1, retry + 1):
                wait = i * 10
                logger.info('等待%d秒' % wait)
                time.sleep(wait)
            return None


def post_one_url(url, data=None):
    # logger.info('爬取url:' + url)
    retry = 3
    success = False
    while not success:
        try:
            resp = requests.post(url, data=data)
            success = True
            if resp.status_code == 200:
                resp.encoding = 'utf-8'  # 解决中文问题
                return resp.text
            return None
        except RequestException:
            logger.error('请求索引页出错')
            for i in range(1, retry + 1):
                wait = i * 10
                logger.info('等待%d秒' % wait)
                time.sleep(wait)
            return None

# def post_one_url(url, data=None):
#     try:
#         resp = requests.post(url, data=data)
#         if resp.status_code == 200:
#             resp.encoding = 'utf-8'  # 解决中文问题
#             return resp.text
#         return None
#     except RequestException:
#         print('请求索引页出错')
#         return None
