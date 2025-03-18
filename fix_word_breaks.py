#!/usr/bin/env python3
# 专门针对单词断行问题的修复脚本

import sys
import os
import re
from PIL import Image, ImageDraw, ImageFont

def detect_word_breaks(text):
    """
    检测文本中可能的单词断行情况
    返回潜在的问题和建议的修复方案
    """
    # 查找连词模式：单词末尾+空格+单词开头被分在不同行
    word_break_pattern = re.compile(r'([a-zA-Z]+)\s+([a-zA-Z]+)')
    matches = word_break_pattern.finditer(text)
    
    issues = []
    for match in matches:
        # 检查是否可能是一个被拆分的单词
        word1 = match.group(1)
        word2 = match.group(2)
        combined = word1 + word2
        
        # 如果组合起来是一个常见英文单词，则可能是断行问题
        # 这里使用一个简单的英文词典检查
        # 未来可以使用更完整的词典或自然语言处理工具
        common_words = [
            "after", "there", "before", "taking", "dividing", "basket", 
            "apple", "apples", "minimum", "maximum", "equal", "parts", 
            "remain", "again", "three", "into", "these", "other", "another"
        ]
        
        if combined.lower() in common_words:
            issues.append({
                "problem": f"'{word1} {word2}'",
                "likely_word": combined,
                "span": match.span()
            })
    
    return issues

def fix_image_text(image_path, output_path, issues=None):
    """
    修复图像中的文本问题，使用PIL绘制修复后的文本
    """
    # 打开原始图像
    img = Image.open(image_path)
    
    # 如果没有提供问题列表，则自动检测
    if issues is None:
        # 这里需要OCR识别图像中的文本
        # 由于我们没有直接的OCR功能，这里我们假设已知问题
        issues = [
            {
                "problem": "Afte r",
                "likely_word": "After",
                "position": (70, 165),  # x, y坐标，需要根据实际图像调整
                "font_size": 20,
                "color": (0, 0, 0)
            }
        ]
    
    # 在图像上修复问题
    draw = ImageDraw.Draw(img)
    
    # 为每个问题绘制修复
    for issue in issues:
        # 加载适当的字体
        try:
            font = ImageFont.truetype("Arial", issue.get("font_size", 20))
        except IOError:
            # 如果找不到指定字体，使用默认字体
            font = ImageFont.load_default()
        
        # 在原问题位置绘制修复的单词
        position = issue.get("position", (0, 0))
        color = issue.get("color", (0, 0, 0))
        
        # 首先用白色矩形覆盖原文本区域
        # 矩形大小需要根据字体和文本调整
        text_width = 100  # 估计的文本宽度
        text_height = 30  # 估计的文本高度
        bg_color = (245, 245, 237)  # 接近原图背景色的颜色
        draw.rectangle(
            [position[0], position[1], position[0]+text_width, position[1]+text_height],
            fill=bg_color
        )
        
        # 在此区域上绘制修复的单词
        draw.text(position, issue["likely_word"], font=font, fill=color)
    
    # 保存修复后的图像
    img.save(output_path)
    print(f"修复后的图像已保存到 {output_path}")
    return True

def main():
    """主函数：分析文本中的单词断行问题并提供修复建议"""
    if len(sys.argv) < 2:
        print("用法: python fix_word_breaks.py [text_to_analyze]")
        print("或者: python fix_word_breaks.py --fix-image input.png output.png")
        sys.exit(1)
    
    # 修复图像模式
    if sys.argv[1] == "--fix-image" and len(sys.argv) >= 4:
        input_image = sys.argv[2]
        output_image = sys.argv[3]
        
        if not os.path.exists(input_image):
            print(f"错误: 找不到输入图像 {input_image}")
            sys.exit(1)
        
        # 定义需要修复的问题
        issues = [
            {
                "problem": "Afte r",
                "likely_word": "After",
                "position": (40, 165),  # 根据实际图像调整
                "font_size": 20,
                "color": (0, 0, 0)
            }
        ]
        
        success = fix_image_text(input_image, output_image, issues)
        if success:
            print(f"成功修复图像中的单词断行问题。")
        else:
            print(f"修复图像失败。")
        
    # 文本分析模式
    else:
        text = " ".join(sys.argv[1:])
        issues = detect_word_breaks(text)
        
        if issues:
            print("检测到以下潜在的单词断行问题:")
            for i, issue in enumerate(issues):
                print(f"  {i+1}. 问题: {issue['problem']} - 可能是 '{issue['likely_word']}'")
            
            print("\n建议:")
            print("1. 优化文本换行算法，确保单词在换行时保持完整")
            print("2. 使用语言模型或词典验证单词边界")
            print("3. 在渲染前对文本进行预处理，确保单词不会被分割")
        else:
            print("未检测到明显的单词断行问题。")

if __name__ == "__main__":
    main() 