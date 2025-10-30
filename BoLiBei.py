#!usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import json
import re
import time
from requests.exceptions import RequestException, ConnectionError, Timeout

__author__ = 'WYY'
__date__ = '2024.10.30'  # 更新日期为当前优化时间


class SCUInfoSpider:
    """爬取SCU-info玻璃杯事件热门评论的爬虫类"""
    # 关键词正则（匹配“玻璃”、“杯”、“摔”、“观光”）
    KEYWORD_PATTERN = re.compile(u'\u73bb\u7483|\u676f|\u6454|\u89c2\u5149', re.S)
    # 请求头（模拟浏览器，避免被反爬）
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01"
    }
    # 基础API地址
    BASE_URL = "http://www.scuinfo.com/api"

    def __init__(self):
        self.start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self.session = requests.Session()  # 复用会话，提高效率
        self.session.adapters.DEFAULT_RETRIES = 3  # 设置重试次数
        print(f"\n开始采集数据\n本地时间：{self.start_time}")

    def fetch_data(self, url, max_retries=2):
        """
        发送请求获取数据，带重试机制
        :param url: 请求地址
        :param max_retries: 最大重试次数
        :return: 解析后的JSON数据或None
        """
        for retry in range(max_retries + 1):
            try:
                response = self.session.get(
                    url,
                    headers=self.HEADERS,
                    timeout=10  # 设置超时时间
                )
                response.raise_for_status()  # 触发HTTP错误状态码异常
                return json.loads(response.text)
            except (ConnectionError, Timeout):
                if retry < max_retries:
                    print(f"网络异常，第{retry + 1}次重试...")
                    time.sleep(1)
                    continue
                print(f"请求{url}失败：网络连接超时")
            except RequestException as e:
                print(f"请求{url}失败：{str(e)}")
            except json.JSONDecodeError:
                print(f"解析{url}返回的JSON失败")
            return None

    def get_latest_post_id(self):
        """获取最新帖子的ID"""
        url = f"{self.BASE_URL}/posts?pageSize=15"
        data = self.fetch_data(url)
        if data and isinstance(data, list) and len(data) > 0:
            return data[0].get('id')
        raise ValueError("无法获取最新帖子ID，请检查API是否可用")

    def collect_relevant_posts(self, start_id=131599):
        """
        收集包含关键词的帖子
        :param start_id: 起始帖子ID
        :return: 符合条件的帖子列表
        """
        try:
            latest_id = self.get_latest_post_id()
        except ValueError as e:
            print(f"初始化失败：{e}")
            return []

        container = []
        total_scanned = 0  # 记录扫描的帖子总数
        print(f"开始扫描帖子（ID范围：{start_id}-{latest_id}）...")

        for post_id in range(start_id, latest_id + 1):
            total_scanned += 1
            url = f"{self.BASE_URL}/post?id={post_id}"
            data = self.fetch_data(url)

            # 跳过无效数据
            if not data or isinstance(data, list):
                if total_scanned % 50 == 0:  # 每扫描50条打印一次进度
                    print(f"已扫描{total_scanned}条帖子，当前ID：{post_id}")
                continue

            # 提取帖子内容（使用get方法避免KeyError）
            body = data.get('body', '')
            like_count = data.get('likeCount', 0)
            comment_count = data.get('commentCount', 0)  # 原代码的comment可能对应此字段

            # 匹配关键词
            if self.KEYWORD_PATTERN.search(body):
                container.append({
                    'body': body,
                    'like': like_count,
                    'comment': comment_count
                })
                print(f"\n发现匹配帖子 #{len(container)}"
                      f"\n内容：{body[:50]}..."  # 只显示前50字避免过长
                      f"\n点赞：{like_count} | 评论：{comment_count}")

            # 控制请求频率（避免给服务器过大压力）
            time.sleep(0.1)  # 延长间隔，原0.01秒太频繁

        end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        print(f"\n扫描完成（{start_id}-{latest_id}）"
              f"\n总扫描帖子：{total_scanned}条"
              f"\n匹配关键词的帖子：{len(container)}条"
              f"\n结束时间：{end_time}")
        return container

    def get_top_comments(self, top_n=100):
        """
        获取按点赞排序的前N条热门评论
        :param top_n: 要返回的热门评论数量
        :return: 排序后的评论列表
        """
        posts = self.collect_relevant_posts()
        if not posts:
            print("没有找到符合条件的帖子")
            return []

        # 先按评论数升序，再按点赞数降序（优先点赞数）
        sorted_posts = sorted(
            posts,
            key=lambda x: (x['comment'], -x['like'])
        )
        # 取前N条
        top_posts = sorted_posts[:top_n]

        print(f"\n人气最高的前{len(top_posts)}条帖子：")
        for idx, post in enumerate(top_posts, 1):
            print(f"\n序号：{idx}"
                  f"\n内容：{post['body']}"
                  f"\n点赞：{post['like']} | 评论：{post['comment']}")
        return top_posts


if __name__ == "__main__":
    try:
        spider = SCUInfoSpider()
        spider.get_top_comments(top_n=100)
    except Exception as e:
        print(f"程序运行出错：{str(e)}")