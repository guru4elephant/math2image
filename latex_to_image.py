import os
import argparse
import subprocess
import tempfile
import random
import math
import re
import textwrap
from pathlib import Path
from pdf2image import convert_from_path
from PIL import Image, ImageChops, ImageFilter, ImageEnhance, ImageDraw, ImageFont
import numpy as np

# 定义可用的字体列表（可根据系统实际可用字体修改）
AVAILABLE_FONTS = [
    "PingFang SC",
    "Songti SC",
    "Heiti SC",
    "STSong",
    "Arial Unicode MS",
]

# 定义类似手写体的字体（可根据系统实际可用字体修改）
HANDWRITING_FONTS = [
    "Xingkai SC",     # 行楷
    "Kaiti SC",       # 楷体
    "STKaiti",        # 华文楷体
    "Songti SC",      # 如果没有专门的手写字体，宋体也可模拟
]

# 定义可用的背景颜色
BACKGROUND_COLORS = [
    "white",              # 默认白色
    "lightgray!20",       # 非常浅的灰色
    "yellow!5",           # 浅黄色
    "orange!3",           # 浅橙色
    "green!2",            # 浅绿色
    "blue!2",             # 浅蓝色
    "red!2",              # 浅红色
    "purple!2",           # 浅紫色
]

def trim_image(image, border=10):
    """
    裁剪图片，去除多余的空白区域，并保留适当的边距
    
    Args:
        image: PIL图像对象
        border: 保留的边距像素数
    
    Returns:
        PIL图像对象: 裁剪后的图像
    """
    # 获取图像背景色（通常为白色）
    bg = Image.new(image.mode, image.size, image.getpixel((0, 0)))
    diff = ImageChops.difference(image, bg)
    
    # 找出非空白区域的边界框
    bbox = diff.getbbox()
    
    if bbox:
        # 添加边距
        bbox = (
            max(0, bbox[0] - border),
            max(0, bbox[1] - border),
            min(image.width, bbox[2] + border),
            min(image.height, bbox[3] + border)
        )
        return image.crop(bbox)
    
    return image


def add_noise(image, intensity=0.05):
    """
    添加噪点到图像
    
    Args:
        image: PIL图像对象
        intensity: 噪点强度 (0-1)
        
    Returns:
        PIL图像对象: 添加噪点后的图像
    """
    # 转换为RGBA以便处理
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    # 创建一个与原图同尺寸的像素数组
    pixel_data = image.load()
    width, height = image.size
    
    # 遍历所有像素并添加随机噪声
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixel_data[x, y]
            
            # 对RGB通道添加随机噪声
            noise = int(intensity * 255 * (random.random() * 2 - 1))
            r = max(0, min(255, r + noise))
            g = max(0, min(255, g + noise))
            b = max(0, min(255, b + noise))
            
            pixel_data[x, y] = (r, g, b, a)
    
    return image


def add_blur(image, radius=0.8):
    """
    对图像应用模糊效果
    
    Args:
        image: PIL图像对象
        radius: 模糊半径
        
    Returns:
        PIL图像对象: 模糊处理后的图像
    """
    return image.filter(ImageFilter.GaussianBlur(radius))


def adjust_brightness(image, factor=1.1):
    """
    调整图像亮度
    
    Args:
        image: PIL图像对象
        factor: 亮度调整因子
        
    Returns:
        PIL图像对象: 亮度调整后的图像
    """
    enhancer = ImageEnhance.Brightness(image)
    return enhancer.enhance(factor)


def adjust_contrast(image, factor=1.1):
    """
    调整图像对比度
    
    Args:
        image: PIL图像对象
        factor: 对比度调整因子
        
    Returns:
        PIL图像对象: 对比度调整后的图像
    """
    enhancer = ImageEnhance.Contrast(image)
    return enhancer.enhance(factor)


def add_paper_texture(image, texture_intensity=0.1):
    """
    添加纸张纹理效果
    
    Args:
        image: PIL图像对象
        texture_intensity: 纹理强度
        
    Returns:
        PIL图像对象: 添加纹理后的图像
    """
    try:
        # 创建一个噪声图像作为纸张纹理
        width, height = image.size
        texture = Image.new('L', (width, height), 255)  # 使用L模式而不是RGB以降低内存使用
        
        # 创建随机噪声作为纹理
        random_noise = np.random.randint(
            low=int(255 * (1 - texture_intensity)), 
            high=255, 
            size=(height, width), 
            dtype=np.uint8
        )
        
        # 将numpy数组转换为PIL图像
        texture = Image.fromarray(random_noise, mode='L')
        
        # 模糊纹理图像以获得更柔和的效果
        texture = texture.filter(ImageFilter.GaussianBlur(1))
        
        # 确保图像模式匹配
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # 将L模式的纹理转换为RGB以匹配原图像
        texture = Image.merge('RGB', [texture, texture, texture])
        
        # 使用MULTIPLY模式将纹理应用到原图像
        result = ImageChops.multiply(image, texture)
        
        return result
    except Exception as e:
        print(f"纸张纹理效果应用失败: {e}")
        # 返回原始图像，而不是中断整个流程
        return image


def apply_lighting_effect(image, intensity=0.1, position='random'):
    """
    添加照明效果
    
    Args:
        image: PIL图像对象
        intensity: 照明强度
        position: 光源位置，'random'或(x, y)坐标
        
    Returns:
        PIL图像对象: 添加照明效果后的图像
    """
    width, height = image.size
    
    # 确定光源位置
    if position == 'random':
        light_x = random.randint(0, width)
        light_y = random.randint(0, height)
    else:
        light_x, light_y = position
    
    # 创建一个渐变光照效果
    light_mask = Image.new('L', (width, height), 0)
    draw = ImageDraw.Draw(light_mask)
    
    # 计算最大距离
    max_dist = math.sqrt(width**2 + height**2)
    
    # 绘制辐射状的光照效果
    for y in range(height):
        for x in range(width):
            # 计算到光源的距离
            dist = math.sqrt((x - light_x)**2 + (y - light_y)**2)
            # 计算光照强度（距离越远越暗）
            light_val = max(0, 255 - int(255 * (dist / max_dist) / (1 - intensity)))
            light_mask.putpixel((x, y), light_val)
    
    # 模糊光照掩码
    light_mask = light_mask.filter(ImageFilter.GaussianBlur(20))
    
    # 创建一个新的亮度增强层
    bright_layer = Image.new('RGB', (width, height), (255, 255, 255))
    
    # 使用光照掩码将增强层应用到原图像
    return Image.composite(bright_layer, image, light_mask)


def add_random_effects(image, effects_config=None):
    """
    应用随机图像效果
    
    Args:
        image: PIL图像对象
        effects_config: 效果配置字典，如果为None则使用随机效果
        
    Returns:
        PIL图像对象: 应用效果后的图像
    """
    # 默认效果配置
    if effects_config is None:
        effects_config = {
            'noise': random.uniform(0, 0.1),
            'blur': random.uniform(0, 0.8),
            'brightness': random.uniform(0.9, 1.1),
            'contrast': random.uniform(0.9, 1.1),
            'texture': random.uniform(0, 0.15),
            'lighting': random.uniform(0, 0.15)
        }
    
    # 应用效果
    if effects_config.get('noise', 0) > 0:
        image = add_noise(image, effects_config['noise'])
    
    if effects_config.get('blur', 0) > 0:
        image = add_blur(image, effects_config['blur'])
    
    if effects_config.get('brightness', 1) != 1:
        image = adjust_brightness(image, effects_config['brightness'])
    
    if effects_config.get('contrast', 1) != 1:
        image = adjust_contrast(image, effects_config['contrast'])
    
    if effects_config.get('texture', 0) > 0:
        image = add_paper_texture(image, effects_config['texture'])
    
    if effects_config.get('lighting', 0) > 0:
        image = apply_lighting_effect(image, effects_config['lighting'])
    
    return image


def format_text_with_line_limit(text, max_chars_per_line):
    """
    根据每行最大字符数对文本进行格式化，保持数学公式完整，并确保英文单词不会被拆分
    
    Args:
        text: 原始文本
        max_chars_per_line: 每行最大字符数
        
    Returns:
        str: 格式化后的文本
    """
    if max_chars_per_line <= 0:
        return text
        
    print(f"原始文本: {text}")
    
    # 使用更智能的方法分行，特殊处理数学公式并保持英文单词完整
    lines = []
    current_line = ""
    i = 0
    
    # 英文单词分隔符
    word_separators = " ,.;:!?-()[]{}\n\t"
    
    while i < len(text):
        # 检查是否是数学公式的开始
        if text[i:i+1] == '$':
            # 查找结束的$
            end_idx = text.find('$', i+1)
            if end_idx != -1:
                # 找到了完整的数学公式
                formula = text[i:end_idx+1]
                
                # 如果当前行加上公式会超过限制，先换行
                if len(current_line) + len(formula) > max_chars_per_line and current_line:
                    lines.append(current_line)
                    current_line = formula
                else:
                    current_line += formula
                
                i = end_idx + 1  # 跳过整个公式
            else:
                # 如果没有找到结束的$，就将$作为普通字符处理
                current_line += text[i]
                i += 1
            continue
            
        # 处理英文单词：如果接下来是一个单词，需要检查是否能完全放入当前行
        if i < len(text) and text[i] not in word_separators:
            # 寻找单词结束位置
            word_end = i
            while word_end < len(text) and text[word_end] not in word_separators:
                word_end += 1
            
            # 提取完整单词
            word = text[i:word_end]
            
            # 判断单词是否需要换行
            if len(current_line) + len(word) > max_chars_per_line:
                # 如果当前行不为空且加上这个单词会超出限制，则换行
                if current_line:
                    lines.append(current_line)
                    current_line = word
                else:
                    # 如果当前行为空，说明单词本身就很长，强制加入当前行
                    current_line = word
                
            else:
                # 单词可以直接加到当前行
                current_line += word
            
            i = word_end  # 移动到单词结束位置
            continue
        
        # 处理分隔符
        current_line += text[i]
        
        # 如果当前字符是换行符或当前行长度达到限制，则换行
        if text[i] == '\n' or len(current_line) >= max_chars_per_line:
            lines.append(current_line)
            current_line = ""
            
            # 如果是因为换行符换行，则移除这个换行符
            if text[i] == '\n':
                current_line = current_line[:-1]
        
        i += 1
    
    # 添加最后一行
    if current_line:
        lines.append(current_line)
    
    formatted_text = '\n'.join(lines)
    print(f"格式化后的文本:\n{formatted_text}")
    return formatted_text


def convert_color_format(color):
    """
    将常见的颜色格式转换为LaTeX兼容的颜色格式
    
    Args:
        color: 颜色字符串，如'rgb(250,248,245)'或'#FFFFFF'
    
    Returns:
        str: LaTeX兼容的颜色格式
    """
    # 处理rgb(r,g,b)格式
    rgb_match = re.match(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', color)
    if rgb_match:
        r, g, b = map(int, rgb_match.groups())
        return f"{{rgb:r,{r};g,{g};b,{b}}}"
    
    # 处理hex格式 (#RRGGBB)
    hex_match = re.match(r'#([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})', color)
    if hex_match:
        r, g, b = [int(x, 16) for x in hex_match.groups()]
        return f"{{rgb:r,{r};g,{g};b,{b}}}"
    
    # 其他格式直接返回
    return color


def render_latex_to_image(
    latex_text, 
    output_path='output.png', 
    dpi=300, 
    template_path=None, 
    auto_trim=True, 
    border=10, 
    use_xelatex=True, 
    main_font="PingFang SC",
    font_size=None,
    random_font=False,
    rotate_angle=0,
    random_rotate=False,
    bg_color=None,
    random_bg_color=False,
    effects=None,
    apply_effects=True,
    max_chars_per_line=-1,
    handwriting=False,
    handwriting_intensity=0.5
):
    """
    将LaTeX文本渲染成图片
    
    Args:
        latex_text (str): LaTeX格式的文本
        output_path (str): 输出图片的路径
        dpi (int): 图片的DPI（分辨率）
        template_path (str): 可选的LaTeX模板路径
        auto_trim (bool): 是否自动裁剪多余的空白区域
        border (int): 裁剪后保留的边距像素数
        use_xelatex (bool): 是否使用XeLaTeX引擎以支持中文
        main_font (str): 主要中文字体名称
        font_size (int): 文字字号，可以是具体的pt值，如11pt，12pt
        random_font (bool): 是否随机选择字体
        rotate_angle (float): 文字旋转角度（度）
        random_rotate (bool): 是否随机旋转文字
        bg_color (str): 背景颜色（LaTeX颜色名称或rgb值）
        random_bg_color (bool): 是否随机背景颜色
        effects (dict): 图像效果配置
        apply_effects (bool): 是否应用图像效果
        max_chars_per_line (int): 每行最大字符数，默认为-1表示不限制
        handwriting (bool): 是否使用手写体效果
        handwriting_intensity (float): 手写效果的强度 (0.0-1.0)
    
    Returns:
        str: 生成的图片路径
    """
    # 如果启用手写体，选择手写体字体并启用相关效果
    if handwriting:
        if random_font or not main_font or main_font not in HANDWRITING_FONTS:
            main_font = random.choice(HANDWRITING_FONTS)
        
        # 手写体通常需要稍大的字号来提高可读性
        if font_size is None:
            font_size = random.choice(['12pt', '14pt'])
            
        # 对于手写体，轻微旋转更自然
        if rotate_angle == 0 and not random_rotate:
            random_rotate = True
            
        # 手写体通常在纸上，所以更自然的背景颜色
        if bg_color is None and not random_bg_color:
            bg_color = random.choice(["white", "yellow!5", "lightgray!10"])
        
        # 确保效果字典存在
        if effects is None:
            effects = {}
    
    # 如果启用随机字体，随机选择一个字体
    if random_font:
        main_font = random.choice(AVAILABLE_FONTS)
    
    # 如果未指定字号，随机选择一个字号
    font_sizes = ['10pt', '11pt', '12pt', '14pt']
    if font_size is None:
        if random.random() < 0.5:  # 有50%概率使用随机字号
            font_size = random.choice(font_sizes)
        else:
            font_size = '11pt'  # 默认字号
    
    # 如果启用随机旋转，随机选择一个旋转角度
    if random_rotate:
        rotate_angle = random.uniform(-5, 5)  # 在-5到5度之间随机选择
    
    # 如果启用随机背景颜色，随机选择一个背景颜色
    if random_bg_color:
        bg_color = random.choice(BACKGROUND_COLORS)
    elif bg_color is None:
        bg_color = "white"  # 默认背景颜色
    else:
        # 转换颜色格式
        bg_color = convert_color_format(bg_color)
    
    # 处理数学公式中的特殊字符，避免丢失
    # 保护数学公式中的$符号
    protected_latex_text = latex_text
    
    # 处理每行最大字符数限制
    if max_chars_per_line > 0:
        print(f"应用行宽限制: max_chars_per_line={max_chars_per_line}")
        protected_latex_text = format_text_with_line_limit(protected_latex_text, max_chars_per_line)
        # 将普通换行符转换为LaTeX的换行命令
        # 在minipage环境中，\par命令是最可靠的换行方式
        # 添加尾部检查，确保不要有悬挂的换行标记
        if protected_latex_text.endswith('\n'):
            protected_latex_text = protected_latex_text[:-1]
        protected_latex_text = protected_latex_text.replace('\n', ' \\par\\vspace{0.5em}\n')
        print(f"添加LaTeX换行命令后:\n{protected_latex_text}")
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        # 生成临时文件名
        tex_file = os.path.join(temp_dir, "latex_content.tex")
        
        # 如果提供了模板，使用模板文件
        if template_path and os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
                # 在模板中替换占位符
                content = template.replace('{{CONTENT}}', protected_latex_text)
                
                # 替换其他配置
                content = content.replace('\\documentclass{article}', f'\\documentclass[{font_size}]{{article}}')
                content = content.replace('\\pagecolor{white}', f'\\pagecolor{{{bg_color}}}')
                
                # 如果需要旋转，添加旋转命令
                if rotate_angle != 0:
                    content = content.replace('{{CONTENT}}', f'\\rotatebox{{{rotate_angle}}}{{{protected_latex_text}}}')
                    # 确保模板加载了rotating包
                    if '\\usepackage{rotating}' not in content:
                        content = content.replace('\\documentclass', '\\usepackage{rotating}\n\\documentclass')
        else:
            # 使用默认的LaTeX模板，包含高级选项
            content = f"""% !TEX program = xelatex
\\documentclass[{font_size}]{{article}}
\\usepackage{{amsmath}}
\\usepackage{{amssymb}}
\\usepackage{{amsfonts}}
\\usepackage{{color}}
\\usepackage[margin=0.5in]{{geometry}}
\\usepackage{{xcolor}}
\\usepackage{{xeCJK}}
\\usepackage{{rotating}}
\\setCJKmainfont{{{main_font}}}
\\setCJKfallbackfamilyfont{{\\CJKrmdefault}}{{Songti SC}}
\\setCJKfallbackfamilyfont{{\\CJKrmdefault}}{{Heiti SC}}
\\pagestyle{{empty}}
\\pagecolor{{{bg_color}}}

\\begin{{document}}
"""
            # 添加文本内容，处理是否需要旋转
            # 不使用center环境，以允许更灵活的文本换行
            if rotate_angle != 0:
                # 对于旋转的文本，我们不直接旋转整个内容，而是分段处理
                content += f"\\rotatebox{{{rotate_angle}}}{{%\n"  # 使用%避免多余的空格
                content += "\\begin{minipage}{0.9\\textwidth}\n"  # 使用minipage环境以支持更好的换行
                content += protected_latex_text
                content += "\n\\end{minipage}%\n}"  # 使用%避免多余的空格
            else:
                content += "\\begin{minipage}{0.9\\textwidth}\n"  # 使用minipage环境以支持更好的换行
                content += protected_latex_text
                content += "\n\\end{minipage}\n"
            
            content += "\n\\end{document}\n"
        
        # 将内容写入临时TeX文件
        with open(tex_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 选择LaTeX编译器
        latex_compiler = 'xelatex' if use_xelatex else 'pdflatex'
        
        # 编译LaTeX文件生成PDF
        try:
            process = subprocess.run(
                [latex_compiler, '-interaction=nonstopmode', '-output-directory=' + temp_dir, tex_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                text=True
            )
            
            # 打印XeLaTeX输出信息，用于调试
            if process.returncode != 0:
                print(f"LaTeX编译警告: {process.stdout}")
                if "CJK" in process.stdout or "font" in process.stdout:
                    print("中文字体加载可能有问题，尝试替代字体...")
                    # 尝试使用替代的中文字体
                    with open(tex_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    content = content.replace(main_font, 'Songti SC')
                    with open(tex_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    # 重新编译
                    process = subprocess.run(
                        [latex_compiler, '-interaction=nonstopmode', '-output-directory=' + temp_dir, tex_file],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        check=False
                    )
                    # 如果还是失败，再尝试Heiti SC
                    if process.returncode != 0:
                        with open(tex_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        content = content.replace('Songti SC', 'Heiti SC')
                        with open(tex_file, 'w', encoding='utf-8') as f:
                            f.write(content)
                        # 重新编译
                        subprocess.run(
                            [latex_compiler, '-interaction=nonstopmode', '-output-directory=' + temp_dir, tex_file],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            check=False
                        )
        except Exception as e:
            print(f"LaTeX编译错误: {e}")
        
        # 生成的PDF文件路径
        pdf_file = os.path.join(temp_dir, "latex_content.pdf")
        
        # 如果PDF文件存在，则转换为图像
        if os.path.exists(pdf_file):
            # 创建输出目录（如果不存在）
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 转换PDF为图像
            try:
                images = convert_from_path(pdf_file, dpi=dpi)
                
                # 保存第一页为图像
                if images:
                    image = images[0]
                    
                    # 自动裁剪多余的空白区域
                    if auto_trim:
                        image = trim_image(image, border=border)
                    
                    # 应用手写体效果
                    if handwriting:
                        print(f"应用手写体效果，强度: {handwriting_intensity}")
                        image = apply_handwriting_effect(image, handwriting_intensity)
                    
                    # 应用特效
                    if apply_effects:
                        image = add_random_effects(image, effects)
                    
                    image.save(output_path)
                    print(f"图片已生成: {output_path}")
                    return output_path
            except Exception as e:
                print(f"PDF转图像错误: {e}")
    
    return None


def list_available_fonts():
    """
    列出系统中可用于LaTeX的中文字体
    """
    try:
        # 使用fc-list命令列出系统中的中文字体
        result = subprocess.run(
            ['fc-list', ':lang=zh', 'family'], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True,
            check=False
        )
        fonts = result.stdout.strip().split('\n')
        
        # 清理字体名称
        clean_fonts = []
        for font in fonts:
            for name in font.split(','):
                clean_name = name.strip()
                if clean_name and clean_name not in clean_fonts:
                    clean_fonts.append(clean_name)
        
        return clean_fonts
    except Exception as e:
        print(f"获取字体列表失败: {e}")
        return AVAILABLE_FONTS


def apply_handwriting_effect(image, intensity=0.5):
    """
    应用手写风格效果，使图像看起来更像手写的
    
    Args:
        image: PIL图像对象
        intensity: 手写效果的强度 (0.0-1.0)
        
    Returns:
        PIL图像对象: 应用手写效果后的图像
    """
    # 1. 轻微旋转整个图像 (0.5-2度)
    rotation_angle = random.uniform(-2, 2) * intensity
    image = image.rotate(rotation_angle, resample=Image.BICUBIC, expand=True, fillcolor=(255, 255, 255))
    
    # 2. 添加轻微的扭曲效果
    width, height = image.size
    
    # 创建扭曲变换网格
    # 对于较低强度，扭曲较少
    x_shift = int(width * 0.02 * intensity)
    y_shift = int(height * 0.02 * intensity)
    
    # 3. 调整对比度，使线条更粗/细
    contrast_factor = 1 + (random.uniform(-0.1, 0.1) * intensity)
    image = adjust_contrast(image, contrast_factor)
    
    # 4. 添加轻微噪点，模拟笔触不均
    noise_intensity = 0.03 * intensity
    image = add_noise(image, noise_intensity)
    
    # 5. 添加轻微的模糊，模拟墨水扩散
    if random.random() < 0.5 * intensity:
        blur_radius = 0.3 * intensity
        image = add_blur(image, blur_radius)
    
    return image


def main():
    parser = argparse.ArgumentParser(description='将LaTeX文本渲染为图片，支持高级图像效果')
    parser.add_argument('--input', '-i', help='输入的LaTeX文本或文件路径')
    parser.add_argument('--output', '-o', default='output.png', help='输出图片的路径')
    parser.add_argument('--dpi', '-d', type=int, default=300, help='图片的DPI（分辨率）')
    parser.add_argument('--template', '-t', help='LaTeX模板文件路径')
    parser.add_argument('--no-trim', action='store_true', help='禁用自动裁剪空白区域')
    parser.add_argument('--border', type=int, default=10, help='裁剪后保留的边距像素数')
    parser.add_argument('--use-pdflatex', action='store_true', help='使用pdflatex而不是xelatex（不支持中文）')
    parser.add_argument('--list-fonts', action='store_true', help='列出系统中可用的中文字体')
    parser.add_argument('--font', default='PingFang SC', help='指定中文字体名称')
    parser.add_argument('--random-font', action='store_true', help='随机选择字体')
    parser.add_argument('--font-size', help='文字字号，如11pt, 12pt等')
    parser.add_argument('--rotate', type=float, default=0, help='文字旋转角度（度）')
    parser.add_argument('--random-rotate', action='store_true', help='随机旋转文字（在-5到5度之间）')
    parser.add_argument('--bg-color', help='背景颜色（LaTeX颜色名称或rgb值）')
    parser.add_argument('--random-bg', action='store_true', help='随机背景颜色')
    parser.add_argument('--add-noise', action='store_true', help='添加噪点效果')
    parser.add_argument('--add-blur', action='store_true', help='添加模糊效果')
    parser.add_argument('--add-texture', action='store_true', help='添加纸张纹理效果')
    parser.add_argument('--add-lighting', action='store_true', help='添加照明效果')
    parser.add_argument('--no-effects', action='store_true', help='禁用所有特效')
    parser.add_argument('--max-chars-per-line', type=int, default=-1, help='每行最大字符数，-1表示不限制')
    parser.add_argument('--handwriting', action='store_true', help='使用手写体效果')
    parser.add_argument('--handwriting-intensity', type=float, default=0.5, help='手写效果的强度 (0.0-1.0)')
    
    args = parser.parse_args()
    
    # 如果请求列出字体
    if args.list_fonts:
        print("系统中可用的中文字体：")
        for font in list_available_fonts():
            print(f"  - {font}")
        return
    
    # 如果输入是文件路径，则读取文件内容
    if args.input and os.path.exists(args.input):
        with open(args.input, 'r', encoding='utf-8') as f:
            latex_text = f.read()
    else:
        latex_text = args.input
    
    if not latex_text:
        print("请提供LaTeX文本或文件路径")
        return
    
    # 添加调试输出：打印原始输入文本
    print(f"DEBUG - 原始输入: '{latex_text}'")
    
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
    
    output_path = render_latex_to_image(
        latex_text, 
        output_path=args.output, 
        dpi=args.dpi,
        template_path=args.template,
        auto_trim=not args.no_trim,
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
        apply_effects=not args.no_effects,
        max_chars_per_line=args.max_chars_per_line,
        handwriting=args.handwriting,
        handwriting_intensity=args.handwriting_intensity
    )
    
    if output_path:
        print(f"图片已生成: {output_path}")
    else:
        print("图片生成失败")


if __name__ == "__main__":
    main() 