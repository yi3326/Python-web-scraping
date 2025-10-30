#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
豆瓣日记关键词提取工具
优化版本：增加了错误处理、配置化、更好的代码结构
"""
import jieba.analyse
import os
import sys
from typing import List, Tuple

__date__ = '2024.01.07'
__author__ = 'WYY'


class KeywordExtractor:
    def __init__(self, stop_words_path: str = None):
        """
        初始化关键词提取器

        Args:
            stop_words_path: 停用词文件路径
        """
        self.stop_words_path = stop_words_path
        self._setup_jieba()

    def _setup_jieba(self):
        """设置结巴分词"""
        try:
            if self.stop_words_path and os.path.exists(self.stop_words_path):
                jieba.analyse.set_stop_words(self.stop_words_path)
                print(f"已加载停用词文件: {self.stop_words_path}")
            else:
                print("未找到停用词文件，将使用默认设置")
        except Exception as e:
            print(f"加载停用词文件失败: {e}")

    def read_file(self, file_path: str) -> str:
        """
        读取文件内容

        Args:
            file_path: 文件路径

        Returns:
            文件内容字符串
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"成功读取文件: {file_path}, 字符数: {len(content)}")
            return content
        except FileNotFoundError:
            print(f"错误: 文件不存在 - {file_path}")
            sys.exit(1)
        except UnicodeDecodeError:
            print(f"错误: 文件编码问题，请确保文件为UTF-8编码 - {file_path}")
            sys.exit(1)
        except Exception as e:
            print(f"读取文件时发生错误: {e}")
            sys.exit(1)

    def extract_keywords(self, content: str, top_k: int = 150,
                         with_weight: bool = True) -> List[Tuple[str, float]]:
        """
        提取关键词

        Args:
            content: 文本内容
            top_k: 返回关键词数量
            with_weight: 是否返回权重

        Returns:
            关键词列表
        """
        try:
            tags = jieba.analyse.extract_tags(
                content,
                topK=top_k,
                withWeight=with_weight
            )
            return tags
        except Exception as e:
            print(f"提取关键词时发生错误: {e}")
            return []

    def save_results(self, tags: List[Tuple[str, float]],
                     output_path: str = None):
        """
        保存结果到文件

        Args:
            tags: 关键词列表
            output_path: 输出文件路径
        """
        if output_path:
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write("关键词\t权重\n")
                    f.write("-" * 30 + "\n")
                    for word, weight in tags:
                        f.write(f"{word}\t{int(weight * 10000)}\n")
                print(f"结果已保存到: {output_path}")
            except Exception as e:
                print(f"保存结果时发生错误: {e}")

    def print_results(self, tags: List[Tuple[str, float]]):
        """打印结果到控制台"""
        print("\n关键词分析结果:")
        print("-" * 40)
        print("关键词\t\t权重")
        print("-" * 40)

        for i, (word, weight) in enumerate(tags, 1):
            # 根据关键词长度调整制表符
            tab_count = 3 if len(word) >= 6 else 4 if len(word) >= 3 else 5
            tabs = '\t' * tab_count
            print(f"{i:2d}. {word}{tabs}{int(weight * 10000)}")

        print(f"\n总计提取出 {len(tags)} 个关键词")


def main():
    """主函数"""
    # 配置文件路径
    INPUT_FILE = r'F:\Desktop\DouBan.txt'
    STOP_WORDS_FILE = r'F:\Desktop\TingYong.txt'
    OUTPUT_FILE = r'F:\Desktop\关键词分析结果.txt'

    # 创建提取器实例
    extractor = KeywordExtractor(STOP_WORDS_FILE)

    # 读取文件
    content = extractor.read_file(INPUT_FILE)

    if not content:
        print("文件内容为空，无法进行分析")
        return

    # 提取关键词
    print("正在分析关键词...")
    tags = extractor.extract_keywords(content, top_k=150, with_weight=True)

    if not tags:
        print("未能提取到关键词")
        return

    # 输出结果
    extractor.print_results(tags)

    # 保存结果
    extractor.save_results(tags, OUTPUT_FILE)


if __name__ == "__main__":
    main()
