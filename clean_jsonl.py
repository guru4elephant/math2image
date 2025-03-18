#!/usr/bin/env python3
# 清理JSONL文件中的非法控制字符
# 用法: python clean_jsonl.py input.jsonl output.jsonl

import sys
import json
import re

def clean_text(text):
    """
    清理文本中的控制字符，确保它们在JSON中被正确转义
    """
    # 将所有控制字符(0-31)转换为适当的转义序列
    # 为了在JSON中保持良好的可读性，我们显式转义一些常见的控制字符
    text = text.replace('\n', '\\n')    # 换行符
    text = text.replace('\r', '\\r')    # 回车符
    text = text.replace('\t', '\\t')    # 制表符
    text = text.replace('\b', '\\b')    # 退格符
    text = text.replace('\f', '\\f')    # 换页符
    
    # 对于其他控制字符(如果有的话)，使用通用转义格式
    def escape_control_chars(match):
        char = match.group(0)
        return '\\u{:04x}'.format(ord(char))
    
    # 匹配所有控制字符(ASCII 0-31)，排除已经转义的字符
    pattern = re.compile(r'[\x00-\x1F]')
    text = pattern.sub(escape_control_chars, text)
    
    return text

def process_file(input_path, output_path):
    """
    处理JSONL文件，清理每行数据中的控制字符
    """
    with open(input_path, 'r', encoding='utf-8') as f_in:
        with open(output_path, 'w', encoding='utf-8') as f_out:
            line_num = 0
            for line in f_in:
                line_num += 1
                if not line.strip():
                    continue  # 跳过空行
                
                try:
                    # 解析JSON行
                    data = json.loads(line)
                    
                    # 清理problem字段中的文本
                    if 'problem' in data:
                        data['problem'] = clean_text(data['problem'])
                    
                    # 清理solution字段中的文本
                    if 'solution' in data:
                        data['solution'] = clean_text(data['solution'])
                    
                    # 输出清理后的JSON
                    f_out.write(json.dumps(data) + '\n')
                    
                except json.JSONDecodeError as e:
                    print(f"Error parsing line {line_num}: {e}")
                    # 尝试修复非JSON格式的行
                    cleaned_line = clean_text(line)
                    try:
                        # 再次尝试解析
                        data = json.loads(cleaned_line)
                        f_out.write(json.dumps(data) + '\n')
                        print(f"Successfully fixed line {line_num}")
                    except json.JSONDecodeError:
                        print(f"Failed to fix line {line_num}, skipping")
                        continue
                        
            print(f"Processing complete. Processed {line_num} lines.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python clean_jsonl.py input.jsonl output.jsonl")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    
    process_file(input_path, output_path)
    print(f"Cleaned JSONL file saved to {output_path}") 