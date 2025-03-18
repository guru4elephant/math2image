#!/usr/bin/env python3
# 测试文本换行函数对英文单词的处理

from latex_to_image import format_text_with_line_limit

# 测试文本，包含问题图片中的文本
test_text = "There is a basket of apples. After dividing them into three equal parts, 2 apples remain. Taking out two of these parts, and dividing them into three equal parts again, 2 apples remain. After taking out two of these parts again and dividing them into three equal parts, 2 apples remain. How many apples are in the basket, at minimum?"

# 不同的行宽限制进行测试
line_widths = [20, 30, 40, 50, 60]

for width in line_widths:
    print("\n" + "=" * 80)
    print(f"测试行宽: {width}个字符")
    print("=" * 80)
    
    formatted_text = format_text_with_line_limit(test_text, width)
    
    # 检查结果中是否有单词被切分
    lines = formatted_text.split('\n')
    for i, line in enumerate(lines):
        print(f"行 {i+1}: {line}")
    
    has_split_word = False
    for i in range(len(lines) - 1):
        if lines[i].strip() and not any(lines[i].endswith(sep) for sep in [' ', '.', ',', ';', ':', '!', '?', '-']):
            if i+1 < len(lines) and lines[i+1].strip() and not lines[i+1].startswith(' '):
                print(f"警告: 可能在行 {i+1} 和行 {i+2} 之间切分了单词!")
                print(f"  行 {i+1}: {lines[i]}")
                print(f"  行 {i+2}: {lines[i+1]}")
                has_split_word = True
    
    if not has_split_word:
        print("✓ 未发现单词被切分的情况")

print("\n完成所有测试") 