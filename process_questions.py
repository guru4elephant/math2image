#!/usr/bin/env python3
import os
import json
import argparse
import random
from tqdm import tqdm
from latex_to_image import render_latex_to_image, BACKGROUND_COLORS

def main():
    parser = argparse.ArgumentParser(description='将JSONL文件中的problem字段转换为图片')
    parser.add_argument('--input', '-i', default='deepscaler_filtered1000.jsonl', help='输入的JSONL文件路径')
    parser.add_argument('--output-dir', '-o', default='simple_question', help='输出图片的目录')
    parser.add_argument('--dpi', '-d', type=int, default=300, help='图片的DPI（分辨率）')
    parser.add_argument('--border', '-b', type=int, default=10, help='图片边框像素数')
    parser.add_argument('--use-pdflatex', action='store_true', help='使用pdflatex而不是xelatex（不支持中文）')
    parser.add_argument('--font', default='PingFang SC', help='指定中文字体名称')
    
    # 高级渲染选项
    parser.add_argument('--font-size', help='字体大小，如11pt, 12pt')
    parser.add_argument('--random-font', action='store_true', help='随机选择字体')
    parser.add_argument('--rotate', type=float, default=0, help='文字旋转角度')
    parser.add_argument('--random-rotate', action='store_true', help='随机旋转文字')
    parser.add_argument('--bg-color', help='背景颜色')
    parser.add_argument('--random-bg', action='store_true', help='随机背景颜色')
    
    # 特效选项
    parser.add_argument('--add-noise', action='store_true', help='添加噪点效果')
    parser.add_argument('--add-blur', action='store_true', help='添加模糊效果')
    parser.add_argument('--add-texture', action='store_true', help='添加纸张纹理效果')
    parser.add_argument('--add-lighting', action='store_true', help='添加照明效果')
    parser.add_argument('--max-chars-per-line', type=int, default=-1, help='每行最大字符数，-1表示不限制')
    
    args = parser.parse_args()
    
    # 确保输出目录存在
    os.makedirs(args.output_dir, exist_ok=True)
    
    # 读取JSONL文件
    questions = []
    with open(args.input, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():  # 忽略空行
                try:
                    question = json.loads(line)
                    questions.append(question)
                except json.JSONDecodeError:
                    print(f"警告: 跳过无效JSON行: {line[:50]}...")
    
    print(f"共读取 {len(questions)} 个问题")
    
    # 配置图像效果
    effects = {}
    if args.add_noise:
        effects['noise'] = 0.05
    if args.add_blur:
        effects['blur'] = 0.5
    if args.add_texture:
        effects['texture'] = 0.1
    if args.add_lighting:
        effects['lighting'] = 0.1
    
    # 处理每个问题
    for i, question in enumerate(tqdm(questions, desc="生成图片")):
        # 获取问题文本
        problem_text = question.get("problem", "")
        
        if not problem_text:
            print(f"警告: 问题 #{i} 没有problem字段，跳过")
            continue
        
        # 生成输出文件名
        output_filename = f"question_{i+1:04d}.png"
        output_path = os.path.join(args.output_dir, output_filename)
        
        # 渲染LaTeX为图片
        render_latex_to_image(
            problem_text, 
            output_path=output_path, 
            dpi=args.dpi,
            border=args.border,
            use_xelatex=not args.use_pdflatex,
            main_font=args.font,
            font_size=args.font_size,
            random_font=args.random_font,
            rotate_angle=args.rotate,
            random_rotate=args.random_rotate,
            bg_color=args.bg_color,
            random_bg_color=args.random_bg,
            effects=effects,
            max_chars_per_line=args.max_chars_per_line
        )
        
        # 保存对应的文本
        text_filename = f"question_{i+1:04d}.txt"
        text_path = os.path.join(args.output_dir, text_filename)
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(problem_text)
        
        # 保存完整的问题数据
        json_filename = f"question_{i+1:04d}.json"
        json_path = os.path.join(args.output_dir, json_filename)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(question, f, ensure_ascii=False, indent=2)
    
    print(f"处理完成，共生成 {len(questions)} 个图片")

if __name__ == "__main__":
    main() 