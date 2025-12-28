#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import time
import requests
from pathlib import Path
from requests.exceptions import RequestException, ConnectionError, Timeout

__author__ = 'WYY'
__date__ = '2024.10.30'  # 更新为当前优化时间


class QiubaiSpider:
    """糗事百科爬虫，支持多页数据爬取、格式化输出与文件保存"""
    # 基础配置
    BASE_URL = "https://www.qiushibaike.com"
    SAVE_DIR = Path("qiubai_data")  # 数据保存目录（脚本所在路径）
    # 现代浏览器请求头，避免被反爬
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": BASE_URL
    }
    # 糗事内容解析正则（适配当前糗事百科列表页结构）
    CONTENT_PATTERN = re.compile(
        r'<div class="article block.*?'  # 单个糗事容器
        r'<h2.*?>(.*?)</h2>'  # 1. 作者名
        r'.*?<div class="articleGender.*?>(.*?)</div>'  # 2. 作者性别/年龄
        r'.*?<div class="content">.*?<span>(.*?)</span>'  # 3. 糗事内容
        r'.*?<i class="number">(.*?)</i>'  # 4. 好笑数
        r'.*?<i class="number">(.*?)</i>'  # 5. 评论数
        r'.*?<i class="number hidden">(.*?)</i>'  # 6. 赞数
        r'.*?<i class="number hidden">(.*?)</i>',  # 7. 踩数
        re.S
    )


    def __init__(self):
        # 初始化会话（复用连接，提升效率）
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        # 创建保存目录（自动处理不存在的情况）
        self.SAVE_DIR.mkdir(parents=True, exist_ok=True)
        print("===== 糗事百科爬虫初始化完成 =====")


    def fetch_html(self, url, max_retries=2):
        """获取网页HTML，带重试机制和异常处理"""
        for retry in range(max_retries + 1):
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()  # 触发HTTP错误（如404、500）
                response.encoding = "utf-8"  # 明确编码，避免乱码
                return response.text
            except (ConnectionError, Timeout):
                if retry < max_retries:
                    print(f"网络异常，第{retry+1}次重试（URL: {url}）...")
                    time.sleep(1)
                    continue
                print(f"请求失败：网络连接超时（URL: {url}）")
            except RequestException as e:
                print(f"请求失败：{str(e)}（URL: {url}）")
            return None


    def clean_text(self, text):
        """清理文本：去除HTML标签、换行符、空格"""
        if not text:
            return "未知"
        # 移除<br>等标签和多余空格
        clean_pattern = re.compile(r'<br\s*/?>|</br>|[\n\r\s]+')
        return re.sub(clean_pattern, ' ', text).strip()


    def parse_qiubai_page(self, html):
        """解析糗事百科页面，提取结构化数据"""
        if not html:
            return []
        
        items = self.CONTENT_PATTERN.findall(html)
        parsed_data = []
        for item in items:
            # 清理每个字段的文本
            author = self.clean_text(item[0])
            gender_age = self.clean_text(item[1])  # 格式如“男 28”
            content = self.clean_text(item[2])
            laugh_count = self.clean_text(item[3]) or "0"
            comment_count = self.clean_text(item[4]) or "0"
            like_count = self.clean_text(item[5]) or "0"
            dislike_count = self.clean_text(item[6]) or "0"

            # 结构化数据，便于后续使用
            parsed_data.append({
                "author": author,
                "gender_age": gender_age,
                "content": content,
                "laugh_count": laugh_count,
                "comment_count": comment_count,
                "like_count": like_count,
                "dislike_count": dislike_count
            })
        return parsed_data


    def format_output(self, parsed_data, page_num):
        """格式化输出糗事数据（控制台友好显示）"""
        if not parsed_data:
            print(f"第{page_num}页未解析到糗事内容")
            return ""
        
        output_text = f"===== 糗事百科第{page_num}页内容（共{len(parsed_data)}条）=====\n"
        for idx, data in enumerate(parsed_data, 1):
            output_text += (
                f"\n{idx}楼\n"
                f"楼主：{data['author']}（{data['gender_age']}）\n"
                f"内容：{data['content']}\n"
                f"好笑：{data['laugh_count']} | 评论：{data['comment_count']} | "
                f"赞：{data['like_count']} | 踩：{data['dislike_count']}\n"
                f"{'='*50}\n"
            )
            # 控制台逐条打印，避免一次性输出过多
            print(
                f"\n{idx}楼\n"
                f"楼主：{data['author']}（{data['gender_age']}）\n"
                f"内容：{data['content']}\n"
                f"好笑：{data['laugh_count']} | 评论：{data['comment_count']}"
            )
            time.sleep(0.1)  # 控制打印速度，提升可读性
        return output_text


    def save_to_file(self, content, page_num):
        """将糗事数据保存到TXT文件（UTF-8编码，避免乱码）"""
        if not content:
            return False
        
        file_path = self.SAVE_DIR / f"qiubai_page{page_num}.txt"
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"\n✅ 第{page_num}页数据已保存至：{file_path.resolve()}")
            return True
        except OSError as e:
            print(f"❌ 保存第{page_num}页文件失败：{str(e)}")
            return False


    def crawl_single_page(self, page_num):
        """爬取单页糗事数据（获取→解析→输出→保存）"""
        print(f"\n===== 开始爬取第{page_num}页 =====")
        # 构建分页URL（第1页URL特殊，无page参数）
        if page_num == 1:
            page_url = self.BASE_URL
        else:
            page_url = f"{self.BASE_URL}/8hr/page/{page_num}/"
        
        # 1. 获取页面HTML
        html = self.fetch_html(page_url)
        if not html:
            print(f"❌ 第{page_num}页爬取失败，跳过该页")
            return False
        
        # 2. 解析页面数据
        parsed_data = self.parse_qiubai_page(html)
        if not parsed_data:
            print(f"❌ 第{page_num}页无有效内容，跳过该页")
            return False
        
        # 3. 格式化输出与保存
        output_content = self.format_output(parsed_data, page_num)
        self.save_to_file(output_content, page_num)
        return True


    def crawl_multi_pages(self, start_page, end_page):
        """爬取多页糗事数据（从start_page到end_page）"""
        # 校验输入参数合法性
        if not (isinstance(start_page, int) and isinstance(end_page, int)):
            print("❌ 页码必须为整数")
            return
        if start_page < 1 or end_page < start_page:
            print(f"❌ 页码范围错误（需满足 1 ≤ 起始页 ≤ 结束页）")
            return
        
        print(f"\n===== 开始批量爬取（第{start_page}页至第{end_page}页）=====")
        success_count = 0  # 成功爬取的页数
        
        for page in range(start_page, end_page + 1):
            if self.crawl_single_page(page):
                success_count += 1
            # 页间等待，避免高频请求被反爬
            if page != end_page:
                wait_time = 2.5  # 等待2.5秒
                print(f"\n等待{wait_time}秒后爬取下一页...")
                time.sleep(wait_time)
        
        # 爬取完成总结
        total_pages = end_page - start_page + 1
        print(f"\n===== 批量爬取结束 =====")
        print(f"总任务：{total_pages}页 | 成功：{success_count}页 | 失败：{total_pages - success_count}页")
        print(f"数据保存目录：{self.SAVE_DIR.resolve()}")


if __name__ == "__main__":
    try:
        # 获取用户输入的页码范围（适配Python3的input）
        start = int(input("请输入起始页数：").strip())
        end = int(input("请输入结束页数：").strip())
        
        # 初始化爬虫并执行
        spider = QiubaiSpider()
        spider.crawl_multi_pages(start, end)
    except ValueError:
        print("❌ 输入错误：页码必须为整数")
    except Exception as e:
        print(f"❌ 程序运行出错：{str(e)}")