#!/bin/bash

# 创建输出目录
mkdir -p output_normal/simple_question
mkdir -p output_real/simple_question

# 初始化JSONL文件
echo "" > output_normal_data.jsonl
echo "" > output_real_data.jsonl

# 参数设置 - 减小边框大小以更紧凑地裁剪
BORDER_SIZE=5
REAL_MODE_BORDER=10
MAX_CHARS_PER_LINE=200
FONT_SIZE=24
REAL_MODE_FONT_SIZE=24

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LATEX_TO_IMAGE_SCRIPT="$SCRIPT_DIR/math2image/latex_to_image.py"

echo "Script directory: $SCRIPT_DIR"
echo "LaTeX to image script: $LATEX_TO_IMAGE_SCRIPT"

# 检查脚本是否存在
if [ ! -f "$LATEX_TO_IMAGE_SCRIPT" ]; then
    echo "Error: LaTeX to image script not found at $LATEX_TO_IMAGE_SCRIPT"
    exit 1
fi

# 创建更精确的Python裁剪脚本
cat > crop_image.py << 'EOF'
#!/usr/bin/env python3
from PIL import Image, ImageChops
import sys
import numpy as np

def trim_image(image_path, output_path, add_border=0):
    """裁剪图片，只保留非空白区域，更精确的算法"""
    try:
        # 打开图片
        img = Image.open(image_path)
        
        # 转换为numpy数组以便更精确处理
        img_array = np.array(img)
        
        # 对于RGB图像
        if len(img_array.shape) == 3:
            # 检测非白色像素 (255,255,255)
            mask = np.any(img_array < 250, axis=2)
        else:
            # 对于灰度图像
            mask = img_array < 250
        
        # 找出非空白区域的坐标
        coords = np.argwhere(mask)
        if len(coords) == 0:
            # 如果没有找到非空白区域，保存原图
            img.save(output_path)
            print("No non-empty area found, saving original image")
            return False
        
        # 找出边界框坐标
        y_min, x_min = coords.min(axis=0)
        y_max, x_max = coords.max(axis=0)
        
        # 添加边距
        x_min = max(0, x_min - add_border)
        y_min = max(0, y_min - add_border)
        x_max = min(img_array.shape[1], x_max + add_border)
        y_max = min(img_array.shape[0], y_max + add_border)
        
        # 裁剪图片
        bbox = (x_min, y_min, x_max, y_max)
        print(f"Found content area: {bbox}")
        cropped = img.crop(bbox)
        
        # 保存裁剪后的图片
        cropped.save(output_path)
        print(f"Image cropped tightly and saved: {output_path}")
        return True
    except Exception as e:
        print(f"Error cropping image: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python crop_image.py input_image output_image [border_size]", file=sys.stderr)
        sys.exit(1)
    
    input_image = sys.argv[1]
    output_image = sys.argv[2]
    border_size = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    
    trim_image(input_image, output_image, border_size)
EOF

chmod +x crop_image.py

# 预处理文本函数
preprocess_text() {
    local text="$1"
    # 替换特殊字符
    text=$(echo "$text" | sed 's/\\n/ /g')
    text=$(echo "$text" | sed 's/\\t/ /g')
    text=$(echo "$text" | sed 's/\\r/ /g')
    echo "$text"
}

# 智能文本换行函数
smart_text_wrap() {
    local text="$1"
    local max_chars="$2"
    local result=""
    local current_line=""
    local in_math=false
    local math_content=""
    
    # 按空格分割文本
    IFS=' ' read -ra words <<< "$text"
    
    for word in "${words[@]}"; do
        # 检查是否在数学公式内
        if [[ "$word" == *"\$"* ]]; then
            # 计算当前词中 $ 的数量
            local dollar_count=$(echo "$word" | grep -o "\$" | wc -l)
            
            # 如果 $ 的数量是奇数，则切换数学模式状态
            if (( dollar_count % 2 == 1 )); then
                in_math=!$in_math
            fi
            
            # 将词添加到当前行
            if [[ -z "$current_line" ]]; then
                current_line="$word"
            else
                current_line="$current_line $word"
            fi
            
            continue
        fi
        
        # 如果在数学公式内，直接添加到当前行
        if $in_math; then
            if [[ -z "$current_line" ]]; then
                current_line="$word"
            else
                current_line="$current_line $word"
            fi
            continue
        fi
        
        # 检查添加新词后当前行的长度
        local new_line
        if [[ -z "$current_line" ]]; then
            new_line="$word"
        else
            new_line="$current_line $word"
        fi
        
        # 如果添加新词后超过最大长度，则换行
        if (( ${#new_line} > max_chars )); then
            # 如果当前行不为空，添加到结果中
            if [[ -n "$current_line" ]]; then
                if [[ -z "$result" ]]; then
                    result="$current_line"
                else
                    result="$result\n$current_line"
                fi
            fi
            current_line="$word"
        else
            current_line="$new_line"
        fi
    done
    
    # 添加最后一行
    if [[ -n "$current_line" ]]; then
        if [[ -z "$result" ]]; then
            result="$current_line"
        else
            result="$result\n$current_line"
        fi
    fi
    
    echo -e "$result"
}

# 处理每个问题
counter=0
while read -r line; do
    ((counter++))
    
    # 解析JSON
    problem_id=$(echo "$line" | jq -r '.id')
    problem_text=$(echo "$line" | jq -r '.problem')
    
    echo "Processing problem $problem_id..."
    echo "Debug: Problem text: $problem_text"
    
    # 预处理文本
    processed_text=$(preprocess_text "$problem_text")
    
    # 智能文本换行
    wrapped_text=$(smart_text_wrap "$processed_text" $MAX_CHARS_PER_LINE)
    
    echo "Debug: Wrapped text: $wrapped_text"
    
    # 生成普通模式图片
    temp_file=$(mktemp)
    echo -e "$wrapped_text" > "$temp_file"
    
    echo "Generating normal mode image..."
    # 使用latex_to_image.py代替math2image命令
    temp_normal_output=$(mktemp).png
    python "$LATEX_TO_IMAGE_SCRIPT" --input "$temp_file" --output "$temp_normal_output" --font-size "${FONT_SIZE}pt" --border $BORDER_SIZE
    
    # 确保输出目录存在
    mkdir -p output_normal/simple_question
    
    # 裁剪普通模式图片 - 更严格的裁剪
    python crop_image.py "$temp_normal_output" "output_normal/simple_question/${problem_id}.png" $BORDER_SIZE
    
    # 添加到JSONL文件
    echo "{\"id\": \"$problem_id\", \"image_path\": \"output_normal/simple_question/${problem_id}.png\", \"problem\": \"$problem_text\"}" >> output_normal_data.jsonl
    
    # 随机选择真实模式效果
    effects=("--handwriting" "--add-blur" "--add-noise" "--add-texture" "--random-rotate" "--handwriting --add-blur" "--handwriting --add-noise" "--handwriting --random-rotate" "--add-blur --add-noise" "--add-noise --random-rotate")
    random_index=$((RANDOM % ${#effects[@]}))
    selected_effect="${effects[$random_index]}"
    
    echo "Generating real mode image with effects: $selected_effect..."
    # 使用latex_to_image.py代替math2image命令
    temp_real_output=$(mktemp).png
    python "$LATEX_TO_IMAGE_SCRIPT" --input "$temp_file" --output "$temp_real_output" --font-size "${REAL_MODE_FONT_SIZE}pt" --border $REAL_MODE_BORDER $selected_effect
    
    # 确保输出目录存在
    mkdir -p output_real/simple_question
    
    # 裁剪真实模式图片 - 更严格的裁剪
    python crop_image.py "$temp_real_output" "output_real/simple_question/${problem_id}.png" $REAL_MODE_BORDER
    
    # 添加到JSONL文件
    echo "{\"id\": \"$problem_id\", \"image_path\": \"output_real/simple_question/${problem_id}.png\", \"problem\": \"$problem_text\", \"effects\": \"$selected_effect\"}" >> output_real_data.jsonl
    
    # 清理临时文件
    rm "$temp_file" "$temp_normal_output" "$temp_real_output" 2>/dev/null
    
    echo "Completed processing problem $problem_id"
done

# 清理裁剪脚本
rm crop_image.py

echo "All processing complete."
echo "Normal mode images: output_normal/simple_question/"
echo "Real mode images: output_real/simple_question/"
echo "Normal mode data: output_normal_data.jsonl"
echo "Real mode data: output_real_data.jsonl" 