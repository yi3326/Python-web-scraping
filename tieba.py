#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__='WYY'
__date__='2017.03.14'

#实战小项目：百度贴吧爬虫
import urllib2
import requests
import re
import os
import time
import random
from bs4 import BeautifulSoup

#定义一个Tool()类方便清洗数据
class Tool():
    removeImg = re.compile('<img.*?>|｛7｝|&nbsp;') # 去除img标签，1-7位空格，&nbsp;
    removeAddr = re.compile('<a.*?>|</a>') # 删除超链接标签
    replaceLine = re.compile('<tr>|<div>|</div>|</p>') # 把换行的标签换位\n
    replaceTD = re.compile('<td>') # 把表格制表<td>换为\t
    replaceBR = re.compile('<br><br>|<br>|</br>|</br></br>') # 把换行符或者双换行符换为\n
    removeExtraTag = re.compile('.*?') # 把其余标签剔除
    removeNoneLine = re.compile('\n+') # 把多余空行删除
    def replace(self, x):
        x = re.sub(self.removeImg, "", x)
        x = re.sub(self.removeAddr, "", x)
        x = re.sub(self.replaceLine, "\n", x)
        x = re.sub(self.replaceTD, "\t", x)
        x = re.sub(self.replaceBR, "\n", x)
        x = re.sub(self.removeExtraTag, "", x)
        x = re.sub(self.removeNoneLine, "\n", x)
        return x.strip() # 把strip()前后多余内容删除

#定义一个Spider类
class Spider():
    #初始化参数
    def __init__(self):
        self.tool = Tool()

    #获取源码
    def getSource(self,url):
        user_agents=['Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20130406 Firefox/23.0','Mozilla/5.0 (Windows NT 6.1; WOW64; rv:18.0) Gecko/20100101 Firefox/18.0','Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/533+ \(KHTML, like Gecko) Element Browser 5.0','IBM WebExplorer /v0.94', 'Galaxy/1.0 [en] (Mac OS X 10.5.6; U; en)','Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)','Opera/9.80 (Windows NT 6.0) Presto/2.12.388 Version/12.14','Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) \Version/6.0 Mobile/10A5355d Safari/8536.25','Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) \Chrome/28.0.1468.0 Safari/537.36','Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0; TheWorld)']
        # user_agent在一堆范围中随机获取
        # random.randint()获取随机数，防止网站认出是爬虫而访问受限
        index=random.randint(0,9)
        user_agent=user_agents[index]
        headers = {'User_agent': user_agent}
        html=requests.get(url,headers=headers)
        return html.text

    #获取帖子标题
    def getTitle(self,url):
        result=self.getSource(url)
        pattern=re.compile('<h1.*?title.*?>(.*?)</h1>',re.S)
        items=re.search(pattern,result)
        print u'这篇帖子标题为：',self.tool.replace(items.group(1))

    #获取帖子总页数
    def getPageNumber(self,url):
        result=self.getSource(url)
        pattern=re.compile('<ul.*?l_posts_num.*?<span class="red">(.*?)</span>',re.S)
        items=re.search(pattern,result).group(1)
        print u'帖子共有',items,u'页'
        return items

    #获取评论内容
    def getContent(self,url):
        result = self.getSource(url)
        pattern=re.compile('<a data-field.*?p_author_name.*?">(.*?)</a>.*?<div id="post_content_.*?>(.*?)</div>',re.S)
        items=re.findall(pattern,result)
        #获取楼层数可以直接用循环，省去正则匹配的麻烦
        number = 1
        for item in items:
            #item[0]为楼主，item[1]为发言内容，使用\n换行符打出内容更干净利落
            #item[1]中可能有img链接，用自定义Tool工具清洗
            print u'\n', number, u'楼', u'\n楼主：', item[0], u'\n内容:', self.tool.replace(item[1])
            time.sleep(0.01)
            number += 1

    #获取晒图,清洗获得链接并保存入list
    def getImage(self,url):
        result=self.getSource(url)
        soup=BeautifulSoup(result,'lxml')
        #此处用BeautifulSoup显然更高效
        #find_all()返回一个list,find()返回一个元素
        #注意class属性和python内置的重合，所以加_变成class_
        items=soup.find_all('img',class_="BDE_Image")
        images=[]
        number=0
        for item in items:
            print u'发现一张图，链接为:',item['src']
            images.append(item['src'])
            number+=1
        if number>=1:
            print u'\n',u'共晒图',number,u'张，厉害了我的哥！！！'
        else:
            print u'喏，没有图......'
        return images

    #创建目录
    def makeDir(self,path):
        self.path=path.strip()
        E=os.path.exists(os.path.join('F:\Desktop\code\LvXingTieBa', self.path))
        if not E:
            #创建新目录,若想将内容保存至别的路径（非系统默认），需要更环境变量
            #更改环境变量用os.chdir()
            os.makedirs(os.path.join('F:\Desktop\code\LvXingTieBa', self.path))
            os.chdir(os.path.join('F:\Desktop\code\LvXingTieBa', self.path))
            print u'正在创建名为',self.path,u'的文件夹'
            return self.path
        else:
            print u'名为',self.path,u'的文件夹已经存在...'
            return False

    #万水千山走遍，接下来就是保存美图
    def saveImage(self,detailURL,name):
        try:
            data=requests.get(detailURL,timeout=10).content
            #保存文件，一定要用绝对路径      `
            #所以设置self.path，是为了方便后面函数无障碍调用
        except requests.exceptions.ConnectionError:
            print u'下载图片失败'
            return None
        fileName = name + '.' + 'jpg'
        f=open(r'F:\Desktop\code\LvXingTieBa\%s\%s'%(self.path,fileName),'wb')
        f.write(data)
        f.close()
        print u'成功保存图片',fileName

    #集合所有的操作,并获取多页
    def getAllPage(self,Num):
        self.siteURL = 'http://tieba.baidu.com/p/' + str(Num)
        #获取帖子标题
        self.getTitle(self.siteURL)
        #获取帖子页数
        numbers=self.getPageNumber(self.siteURL)
        for page in range(1,int(numbers)+1):
            #格式化索引链接
            self.url=self.siteURL+'?pn='+str(page)
            print u'\n\n',u'正准备获取第',page,u'页的内容...'
            #获取评论
            print u'\n',u'正准备获取评论...'
            self.getContent(self.url)
            #每一页创建一个文件
            self.makeDir(path='page'+str(page))
            #获取图片
            print u'\n',u'正准备获取图片...'
            images=self.getImage(self.url)
            print u'\n',u'正准备保存图片...'
            number=1
            #保存图片，先从之前的list中找链接
            for detailURL in images:
                name='page'+str(page)+'num'+str(number)
                self.saveImage(detailURL,name)
                time.sleep(0.1)
                number+=1

            print u'\n\n',u'完成第',page,u'页'
        print u'\n\n',u'恭喜，圆满成功！'

#raw_input()实现和外部交互，想看哪个贴就看哪个贴
Num=int(raw_input(u'您好，输入帖子号：'))
spider=Spider()
spider.getAllPage(Num)


# #!/usr/bin/env python
# # -*- coding: utf-8 -*-
# """
# 百度贴吧爬虫工具
# 功能：爬取贴吧帖子内容、图片，并保存到本地
# 作者：WYY
# 日期：2017.03.14
# 优化日期：2024.01.20
# """

# import urllib2
# import requests
# import re
# import os
# import time
# import random
# import logging
# from bs4 import BeautifulSoup
# from typing import List, Tuple, Optional, Dict, Any


# class Tool:
#     """
#     数据清洗工具类
#     用于清洗HTML标签和格式化文本内容
#     """
    
#     def __init__(self):
#         # 定义各种正则表达式模式用于清洗数据
#         self.removeImg = re.compile(r'<img.*?>| {1,7}|&nbsp;')  # 去除img标签，1-7位空格，&nbsp;
#         self.removeAddr = re.compile(r'<a.*?>|</a>')  # 删除超链接标签
#         self.replaceLine = re.compile(r'<tr>|<div>|</div>|</p>')  # 把换行的标签换为\n
#         self.replaceTD = re.compile(r'<td>')  # 把表格制表<td>换为\t
#         self.replaceBR = re.compile(r'<br><br>|<br>|</br>|</br></br>')  # 把换行符或者双换行符换为\n
#         self.removeExtraTag = re.compile(r'<.*?>')  # 把其余标签剔除
#         self.removeNoneLine = re.compile(r'\n+')  # 把多余空行删除
    
#     def replace(self, text: str) -> str:
#         """
#         清洗HTML文本
        
#         Args:
#             text: 待清洗的HTML文本
            
#         Returns:
#             清洗后的纯文本
#         """
#         if not text:
#             return ""
            
#         text = re.sub(self.removeImg, "", text)
#         text = re.sub(self.removeAddr, "", text)
#         text = re.sub(self.replaceLine, "\n", text)
#         text = re.sub(self.replaceTD, "\t", text)
#         text = re.sub(self.replaceBR, "\n", text)
#         text = re.sub(self.removeExtraTag, "", text)
#         text = re.sub(self.removeNoneLine, "\n", text)
#         return text.strip()


# class Spider:
#     """
#     贴吧爬虫主类
#     负责爬取帖子内容、图片并保存到本地
#     """
    
#     def __init__(self, base_path: str = None, max_retries: int = 3):
#         """
#         初始化爬虫
        
#         Args:
#             base_path: 文件保存的基础路径
#             max_retries: 最大重试次数
#         """
#         self.tool = Tool()
#         self.session = requests.Session()
#         self.max_retries = max_retries
        
#         # 设置基础保存路径
#         if base_path is None:
#             self.base_path = os.path.join(os.path.expanduser('~'), 'TiebaSpider')
#         else:
#             self.base_path = base_path
            
#         # 创建基础目录
#         if not os.path.exists(self.base_path):
#             os.makedirs(self.base_path)
            
#         # 配置日志
#         self._setup_logging()
        
#         # User-Agent列表
#         self.user_agents = [
#             'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
#             'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
#             'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
#             'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
#             'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
#         ]
        
#         logging.info(f"爬虫初始化完成，文件将保存到: {self.base_path}")
    
#     def _setup_logging(self):
#         """配置日志系统"""
#         log_path = os.path.join(self.base_path, 'spider.log')
#         logging.basicConfig(
#             level=logging.INFO,
#             format='%(asctime)s - %(levelname)s - %(message)s',
#             handlers=[
#                 logging.FileHandler(log_path, encoding='utf-8'),
#                 logging.StreamHandler()
#             ]
#         )
    
#     def _get_random_delay(self) -> float:
#         """获取随机延迟时间"""
#         return random.uniform(0.5, 2.0)
    
#     def get_source(self, url: str) -> Optional[str]:
#         """
#         获取网页源码
        
#         Args:
#             url: 目标URL
            
#         Returns:
#             网页源码文本，失败返回None
#         """
#         for attempt in range(self.max_retries):
#             try:
#                 # 随机选择User-Agent
#                 user_agent = random.choice(self.user_agents)
#                 headers = {
#                     'User-Agent': user_agent,
#                     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
#                     'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
#                     'Accept-Encoding': 'gzip, deflate',
#                     'Connection': 'keep-alive',
#                     'Upgrade-Insecure-Requests': '1',
#                 }
                
#                 response = self.session.get(url, headers=headers, timeout=10)
#                 response.raise_for_status()
#                 response.encoding = 'utf-8'
                
#                 logging.info(f"成功获取页面: {url}")
#                 return response.text
                
#             except requests.exceptions.RequestException as e:
#                 logging.warning(f"第{attempt + 1}次获取页面失败: {url}, 错误: {e}")
#                 if attempt < self.max_retries - 1:
#                     delay = self._get_random_delay() * (attempt + 1)
#                     logging.info(f"等待{delay:.2f}秒后重试...")
#                     time.sleep(delay)
#                 else:
#                     logging.error(f"获取页面失败，已达到最大重试次数: {url}")
#                     return None
    
#     def get_title(self, url: str) -> Optional[str]:
#         """
#         获取帖子标题
        
#         Args:
#             url: 帖子URL
            
#         Returns:
#             帖子标题，失败返回None
#         """
#         result = self.get_source(url)
#         if not result:
#             return None
            
#         try:
#             pattern = re.compile(r'<h1.*?class="core_title_txt.*?title="(.*?)".*?>', re.S)
#             match = re.search(pattern, result)
#             if match:
#                 title = self.tool.replace(match.group(1))
#                 logging.info(f"帖子标题: {title}")
#                 return title
#             else:
#                 logging.warning("未找到帖子标题")
#                 return None
#         except Exception as e:
#             logging.error(f"解析帖子标题失败: {e}")
#             return None
    
#     def get_page_number(self, url: str) -> int:
#         """
#         获取帖子总页数
        
#         Args:
#             url: 帖子URL
            
#         Returns:
#             总页数，失败返回1
#         """
#         result = self.get_source(url)
#         if not result:
#             return 1
            
#         try:
#             # 尝试多种方式获取页数
#             patterns = [
#                 re.compile(r'<span class="red">(\d+)</span>', re.S),
#                 re.compile(r'共(\d+)页', re.S),
#                 re.compile(r'">(\d+)</a></span><a', re.S)
#             ]
            
#             for pattern in patterns:
#                 match = re.search(pattern, result)
#                 if match:
#                     page_num = int(match.group(1))
#                     logging.info(f"帖子共有 {page_num} 页")
#                     return page_num
            
#             logging.info("未找到分页信息，默认为1页")
#             return 1
            
#         except Exception as e:
#             logging.error(f"解析页数失败: {e}")
#             return 1
    
#     def get_content(self, url: str) -> List[Tuple[str, str]]:
#         """
#         获取帖子评论内容
        
#         Args:
#             url: 帖子页面URL
            
#         Returns:
#             包含(楼主, 内容)的元组列表
#         """
#         result = self.get_source(url)
#         if not result:
#             return []
            
#         try:
#             pattern = re.compile(
#                 r'<a.*?class="p_author_name.*?">(.*?)</a>.*?'
#                 r'<div id="post_content_.*?>(.*?)</div>',
#                 re.S
#             )
#             items = re.findall(pattern, result)
            
#             contents = []
#             for i, (author, content) in enumerate(items, 1):
#                 clean_content = self.tool.replace(content)
#                 contents.append((author, clean_content))
#                 logging.debug(f"第{i}楼 - 作者: {author}")
            
#             logging.info(f"成功获取 {len(contents)} 条评论")
#             return contents
            
#         except Exception as e:
#             logging.error(f"解析评论内容失败: {e}")
#             return []
    
#     def get_images(self, url: str) -> List[str]:
#         """
#         获取帖子中的图片链接
        
#         Args:
#             url: 帖子页面URL
            
#         Returns:
#             图片URL列表
#         """
#         result = self.get_source(url)
#         if not result:
#             return []
            
#         try:
#             soup = BeautifulSoup(result, 'lxml')
#             # 查找所有图片标签
#             img_tags = soup.find_all('img', class_="BDE_Image")
            
#             images = []
#             for img in img_tags:
#                 if img.get('src'):
#                     images.append(img['src'])
            
#             logging.info(f"发现 {len(images)} 张图片")
#             return images
            
#         except Exception as e:
#             logging.error(f"解析图片链接失败: {e}")
#             return []
    
#     def make_dir(self, dir_name: str) -> bool:
#         """
#         创建目录
        
#         Args:
#             dir_name: 目录名称
            
#         Returns:
#             创建成功返回True，否则返回False
#         """
#         try:
#             dir_path = os.path.join(self.base_path, dir_name.strip())
            
#             if not os.path.exists(dir_path):
#                 os.makedirs(dir_path)
#                 logging.info(f"创建目录: {dir_path}")
#                 return True
#             else:
#                 logging.info(f"目录已存在: {dir_path}")
#                 return True
                
#         except Exception as e:
#             logging.error(f"创建目录失败: {e}")
#             return False
    
#     def save_image(self, image_url: str, save_path: str) -> bool:
#         """
#         保存图片到本地
        
#         Args:
#             image_url: 图片URL
#             save_path: 保存路径
            
#         Returns:
#             保存成功返回True，否则返回False
#         """
#         for attempt in range(self.max_retries):
#             try:
#                 headers = {'User-Agent': random.choice(self.user_agents)}
#                 response = self.session.get(image_url, headers=headers, timeout=15)
#                 response.raise_for_status()
                
#                 with open(save_path, 'wb') as f:
#                     f.write(response.content)
                
#                 logging.info(f"成功保存图片: {save_path}")
#                 return True
                
#             except Exception as e:
#                 logging.warning(f"第{attempt + 1}次保存图片失败: {image_url}, 错误: {e}")
#                 if attempt < self.max_retries - 1:
#                     time.sleep(self._get_random_delay())
        
#         logging.error(f"保存图片失败，已达到最大重试次数: {image_url}")
#         return False
    
#     def save_content_to_file(self, contents: List[Tuple[str, str]], file_path: str):
#         """
#         保存文本内容到文件
        
#         Args:
#             contents: 内容列表
#             file_path: 文件保存路径
#         """
#         try:
#             with open(file_path, 'w', encoding='utf-8') as f:
#                 f.write("贴吧帖子内容\n")
#                 f.write("=" * 50 + "\n\n")
                
#                 for i, (author, content) in enumerate(contents, 1):
#                     f.write(f"第{i}楼\n")
#                     f.write(f"作者: {author}\n")
#                     f.write(f"内容: {content}\n")
#                     f.write("-" * 30 + "\n\n")
            
#             logging.info(f"成功保存文本内容到: {file_path}")
#         except Exception as e:
#             logging.error(f"保存文本内容失败: {e}")
    
#     def get_all_page(self, post_id: int, start_page: int = 1, end_page: int = None):
#         """
#         获取帖子的所有内容
        
#         Args:
#             post_id: 帖子ID
#             start_page: 开始页码
#             end_page: 结束页码
#         """
#         base_url = f'https://tieba.baidu.com/p/{post_id}'
        
#         logging.info(f"开始爬取帖子: {post_id}")
        
#         # 获取帖子标题
#         title = self.get_title(base_url)
#         if title:
#             # 创建帖子主目录
#             safe_title = re.sub(r'[\\/*?:"<>|]', "", title)[:50]  # 清理非法字符并截断
#             post_dir = f"{post_id}_{safe_title}"
#             self.make_dir(post_dir)
        
#         # 获取总页数
#         total_pages = self.get_page_number(base_url)
        
#         if end_page is None or end_page > total_pages:
#             end_page = total_pages
        
#         logging.info(f"计划爬取第{start_page}页到第{end_page}页，共{end_page - start_page + 1}页")
        
#         for page in range(start_page, end_page + 1):
#             logging.info(f"正在处理第{page}页...")
            
#             # 构建页面URL
#             page_url = f'{base_url}?pn={page}'
            
#             # 随机延迟
#             time.sleep(self._get_random_delay())
            
#             # 获取评论内容
#             contents = self.get_content(page_url)
            
#             # 获取图片
#             images = self.get_images(page_url)
            
#             # 创建页面目录
#             page_dir_name = f"page_{page}"
#             page_dir_path = os.path.join(self.base_path, post_dir, page_dir_name)
#             self.make_dir(page_dir_path)
            
#             # 保存文本内容
#             if contents:
#                 content_file = os.path.join(page_dir_path, f"content_page_{page}.txt")
#                 self.save_content_to_file(contents, content_file)
            
#             # 保存图片
#             if images:
#                 logging.info(f"开始保存第{page}页的{len(images)}张图片...")
#                 for i, img_url in enumerate(images, 1):
#                     img_name = f"image_{i}.jpg"
#                     img_path = os.path.join(page_dir_path, img_name)
#                     self.save_image(img_url, img_path)
                    
#                     # 图片下载间隔
#                     time.sleep(self._get_random_delay() / 2)
            
#             logging.info(f"第{page}页处理完成")
        
#         logging.info(f"帖子 {post_id} 爬取完成！")


# def main():
#     """主函数"""
#     print("=" * 50)
#     print("百度贴吧爬虫工具")
#     print("=" * 50)
    
#     try:
#         # 获取用户输入
#         post_id = input("请输入贴吧帖子ID: ").strip()
#         if not post_id.isdigit():
#             print("错误：帖子ID必须是数字！")
#             return
        
#         start_page = input("请输入开始页码(默认为1): ").strip()
#         start_page = int(start_page) if start_page.isdigit() else 1
        
#         end_page = input("请输入结束页码(默认为全部): ").strip()
#         end_page = int(end_page) if end_page.isdigit() else None
        
#         # 创建爬虫实例
#         spider = Spider()
        
#         # 开始爬取
#         spider.get_all_page(int(post_id), start_page, end_page)
        
#         print("\n爬取完成！")
#         print(f"文件保存在: {spider.base_path}")
        
#     except KeyboardInterrupt:
#         print("\n用户中断操作")
#     except Exception as e:
#         print(f"程序执行出错: {e}")


# if __name__ == '__main__':
#     main()


