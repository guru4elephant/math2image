#!/usr/bin/env python3
import json
import sys

# 检查JSONL文件格式
def check_jsonl(file_path):
    print(f"检查文件: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        # 读取前两行
        for i, line in enumerate(f):
            if i >= 2:  # 只检查前两条记录
                break
                
            try:
                print(f"\n记录 #{i+1} (原始JSON字符串前100个字符):")
                print(line[:100] + "...")
                
                data = json.loads(line)
                print(f"ID: {data['id']}")
                print(f"图片路径: {data['image']}")
                
                # 打印对话部分，替换\n为[NEWLINE]以便可视化
                human_value = data['conversations'][0]['value']
                gpt_value = data['conversations'][1]['value']
                
                print("\n人类提示 (前100个字符，换行符可视化):")
                print(human_value[:100].replace('\n', '[NEWLINE]'))
                
                print("\n人类提示中的换行符数量:", human_value.count('\n'))
                
                # 检查换行符在原始JSON中的表示
                newline_repr = r'\n'
                backslash_n_count = line.count(newline_repr)
                print(f"原始JSON中'\\n'的出现次数: {backslash_n_count}")
                
                print("\nGPT回答:")
                print(gpt_value.replace('\n', '[NEWLINE]'))
                
            except json.JSONDecodeError as e:
                print(f"解析错误: {e}")
                print(f"问题行: {line[:100]}...")
    
    # 额外的统计
    print("\n文件统计:")
    with open(file_path, 'r', encoding='utf-8') as f:
        total_lines = sum(1 for _ in f)
    print(f"总记录数: {total_lines}")
    
    print("\nJSONL格式检查完成")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        check_jsonl(sys.argv[1])
    else:
        print("请提供JSONL文件路径")
        print("用法: python check_jsonl.py output_normal_data.jsonl") 