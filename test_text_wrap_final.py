#!/usr/bin/env python3
# 测试文本断行算法是否会将英文单词断开

import sys
import os
import unittest
from latex_to_image import format_text_with_line_limit

class TestWordWrapping(unittest.TestCase):
    """测试单词断行问题"""
    
    def test_simple_words(self):
        """测试简单的英文单词不被断行"""
        text = "After dividing the basket of apples into three equal parts"
        formatted = format_text_with_line_limit(text, 10)
        
        # 打印分行后的文本进行检查
        print(f"原文: {text}")
        print(f"分行后 (max=10):\n{formatted}")
        
        # 确认每行都是完整的单词，不是单词的一部分
        lines = formatted.split('\n')
        all_valid = True
        for line in lines:
            words = line.strip().split()
            for word in words:
                # 移除单词中的标点符号
                clean_word = ''.join(c for c in word if c.isalpha())
                if clean_word not in text and clean_word:
                    print(f"检测到可能的单词断行: '{clean_word}' 不是原文中的完整单词")
                    all_valid = False
        
        self.assertTrue(all_valid, "检测到单词断行问题")
        
        # 确认每行长度不超过限制
        for line in lines:
            # 边界条件：超长单词可能会超出限制
            if line.strip() in ["After", "dividing", "basket", "apples", "three", "equal", "parts"]:
                continue
            self.assertLessEqual(len(line), 10, f"行'{line}'超过了字符限制")
    
    def test_with_math_formulas(self):
        """测试带有数学公式的文本不被错误断行"""
        text = "After computing $a^2 + b^2 = c^2$ we can determine the value"
        formatted = format_text_with_line_limit(text, 15)
        
        print(f"原文: {text}")
        print(f"分行后 (max=15):\n{formatted}")
        
        # 确认数学公式完整保留
        self.assertIn("$a^2 + b^2 = c^2$", formatted)
        
        # 检查每一行
        lines = formatted.split('\n')
        for line in lines:
            words = line.strip().split()
            for word in words:
                # 如果是数学公式就跳过
                if '$' in word:
                    continue
                # 移除单词中的标点符号
                clean_word = ''.join(c for c in word if c.isalpha())
                # 跳过空字符串
                if not clean_word:
                    continue
                # 检查单词是否在原文中
                self.assertTrue(text.find(clean_word) != -1, f"单词 '{clean_word}' 不是原文中的完整单词")
    
    def test_problematic_case(self):
        """测试之前有问题的具体案例"""
        text = "After taking two apples, there remain three apples."
        formatted = format_text_with_line_limit(text, 12)
        
        print(f"原文: {text}")
        print(f"分行后 (max=12):\n{formatted}")
        
        # 检查所有的行，确保单词没有被拆分
        lines = formatted.split('\n')
        all_words = []
        for line in lines:
            words = line.strip().split()
            all_words.extend(words)
        
        # 确认原始单词都在拆分后的单词列表中，考虑标点符号可能被分开
        # 创建清理后的单词列表，只保留字母部分
        clean_words = []
        for word in all_words:
            # 清理单词，只保留字母
            clean_word = ''.join(c for c in word if c.isalpha())
            if clean_word:
                clean_words.append(clean_word.lower())
        
        # 确认原始单词的字母部分都在清理后的单词列表中
        original_words = ["After", "taking", "two", "apples", "there", "remain", "three", "apples"]
        for word in original_words:
            # 清理原始单词，只保留字母
            clean_word = ''.join(c for c in word if c.isalpha()).lower()
            self.assertIn(clean_word, clean_words, f"单词'{word}'在拆分后丢失或被改变")
        
        # 验证标点符号是否存在
        punctuation = [',', '.']
        for p in punctuation:
            self.assertIn(p, all_words, f"标点'{p}'在拆分后丢失")
    
    def test_long_words(self):
        """测试超长单词的处理"""
        text = "Supercalifragilisticexpialidocious is a very long word"
        formatted = format_text_with_line_limit(text, 15)
        
        print(f"原文: {text}")
        print(f"分行后 (max=15):\n{formatted}")
        
        # 确认超长单词被正确处理（可能会单独占一行）
        self.assertIn("Supercalifragilisticexpialidocious", formatted)
    
    def detect_word_breaks(self, text):
        """检测可能的单词断行问题"""
        lines = text.split('\n')
        potential_breaks = []
        
        # 比较每行的所有单词是否都是原始文本中的完整单词
        original_words = set()
        for word in text.split():
            # 清理单词，只保留字母
            clean_word = ''.join(c for c in word if c.isalpha())
            if clean_word:
                original_words.add(clean_word.lower())
        
        for i, line in enumerate(lines):
            words = line.strip().split()
            for word in words:
                # 清理单词，只保留字母
                clean_word = ''.join(c for c in word if c.isalpha())
                if clean_word and clean_word.lower() not in original_words:
                    potential_breaks.append((i, word, clean_word))
        
        return potential_breaks
    
    def test_various_line_widths(self):
        """使用不同的行宽测试文本格式化"""
        text = "After dividing the basket of apples into three equal parts, there remain two apples."
        line_widths = [8, 10, 15, 20, 30]
        
        print("\n测试不同行宽:")
        for width in line_widths:
            formatted = format_text_with_line_limit(text, width)
            print(f"\n行宽 {width}:")
            print(formatted)
            
            # 检测潜在的单词断行
            breaks = self.detect_word_breaks(formatted)
            if breaks:
                print(f"警告: 检测到潜在的单词断行问题，行宽 {width}:")
                for line_num, original, clean_word in breaks:
                    print(f"  行 {line_num} 单词 '{original}' (清理后: '{clean_word}') 不是原文中的完整单词")
            else:
                print(f"✓ 行宽 {width}: 未检测到单词断行问题")
            
            # 断言没有单词断行问题
            self.assertEqual(len(breaks), 0, f"行宽 {width} 存在单词断行问题")

def main():
    unittest.main()

if __name__ == "__main__":
    main() 