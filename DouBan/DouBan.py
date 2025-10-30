#!/usr/bin/env python
# -*- coding: utf-8 -*-
__date__ = '2017.04.06'
__author__ = 'WYY'

import requests
import json
import re
from bs4 import BeautifulSoup
import itertools
import time
import xlwt
import os


class Tool():
    def replace(self, x):
        x = re.sub(re.compile('<br>|</br>|&nbsp;|<p>|</p>|<td>|</td>|<tr>|</tr>|</a>|<table>|</table>'), "", x)
        x = re.sub(re.compile('<div.*?>|<img.*?>|<a.*?>|<td.*?>'), "", x)
        return x.strip()


class Spider():
    def __init__(self):
        self.tool = Tool()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def get_source(self, url):
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()  # 检查请求是否成功
            return response
        except requests.exceptions.RequestException as e:
            print(f"请求失败: {e}")
            return None

    def get_main(self):
        mains = []
        print(u'\n', u'正在解析页面...')

        for i in range(0, 2001, 20):  # 从0开始
            print(f"正在获取第 {i // 20 + 1} 页...")
            url = f'https://www.douban.com/j/search?q=张国荣&start={i}&cat=1015'
            response = self.get_source(url)

            if response is None:
                print(f"第 {i // 20 + 1} 页获取失败，跳过")
                continue

            try:
                data = json.loads(response.text)
                main = data.get('items', [])
                if main:
                    mains.append(main)
                else:
                    print(f"第 {i // 20 + 1} 页无数据，可能已到末尾")
                    break
            except json.JSONDecodeError:
                print(f"第 {i // 20 + 1} 页JSON解析失败")
                continue

            time.sleep(1)  # 增加延迟避免被封

        print(u'\n', u'解析页面完成！')
        return mains

    def get_link(self):
        n = 1
        links = []
        mains = self.get_main()
        print(u'正在获取链接...')

        for main in mains:
            for j in range(len(main)):
                try:
                    soup = BeautifulSoup(main[j], 'html.parser')
                    h3_tag = soup.find('h3')
                    if h3_tag:
                        a_tag = h3_tag.find('a')
                        if a_tag and 'href' in a_tag.attrs:
                            href = a_tag['href']
                            # 从href中提取note id
                            note_id_match = re.search(r'note/(\d+)/', href)
                            if note_id_match:
                                note_id = note_id_match.group(1)
                                link = f'https://www.douban.com/note/{note_id}/'
                                print(f"{n}. {link}")
                                links.append(link)
                                n += 1
                except Exception as e:
                    print(f"解析链接时出错: {e}")
                    continue

        print(u'\n', u'成功将所有链接存入list!', u'\n', u'一共', len(links), u'项')
        return links

    def get_detail(self):
        links = self.get_link()
        container = []
        print(u'\n', u'正在获取详细信息...')

        for i, link in enumerate(links, 1):
            print(f"正在处理第 {i}/{len(links)} 项: {link}")
            response = self.get_source(link)

            if response is None:
                print(f"第 {i} 项获取失败，跳过")
                continue

            html = response.text
            data = []

            try:
                soup = BeautifulSoup(html, 'html.parser')

                # 获取标题
                title_tag = soup.find('h1')
                title = title_tag.get_text().strip() if title_tag else "无标题"

                # 获取作者
                author_tag = soup.find('a', class_='note-author')
                author = author_tag.get_text().strip() if author_tag else "未知作者"

                # 获取发布时间
                date_tag = soup.find('span', class_='pub-date')
                pub_date = date_tag.get_text().strip() if date_tag else "未知时间"

                # 获取喜欢数量
                fav_tag = soup.find('span', class_='fav-num')
                fav_num = fav_tag.get_text().strip() if fav_tag else "0"

                # 获取内容
                content_tag = soup.find('div', class_='note')
                content = content_tag.get_text().strip() if content_tag else "无内容"
                content = self.tool.replace(content)

                data = [title, link, author, pub_date, fav_num, content]
                container.append(data)

            except Exception as e:
                print(f"解析第 {i} 项详情时出错: {e}")
                continue

            time.sleep(2)  # 增加延迟

        print(u'\n', u'成功获取所有信息！')
        return container

    def save_detail(self):
        container = self.get_detail()

        if not container:
            print("没有获取到数据，无法保存")
            return

        # 保存到Excel
        book = xlwt.Workbook(encoding='utf-8')
        sheet = book.add_sheet('豆瓣日记', cell_overwrite_ok=True)
        heads = [u'标题', u'链接', u'作者', u'发布时间', u'喜欢数量', u'内容']

        # 写入表头
        for i, head in enumerate(heads):
            sheet.write(0, i, head)

        # 写入数据
        for i, item in enumerate(container, 1):
            for j, data in enumerate(item):
                try:
                    sheet.write(i, j, data)
                except:
                    sheet.write(i, j, str(data))

        # 保存文件
        excel_filename = 'DouBan_张国荣日记.xls'
        book.save(excel_filename)
        print(f'\nExcel文件已保存: {excel_filename}')

        # 保存到TXT
        txt_filename = 'DouBan_张国荣日记.txt'
        with open(txt_filename, 'w', encoding='utf-8') as f:
            for item in container:
                # 只保存内容到txt
                f.write(item[5] + '\n' + '=' * 50 + '\n')
        print(f'TXT文件已保存: {txt_filename}')


if __name__ == "__main__":
    spider = Spider()
    spider.save_detail()