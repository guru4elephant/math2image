#!/usr/bin/env python3
from PIL import Image, ImageChops

def trim_image(image_path, output_path, add_border=0):
    """裁剪图片，只保留非空白区域"""
    try:
        # 打开图片
        img = Image.open(image_path)
        
        # 获取图像背景色（通常为白色）
        bg = Image.new(img.mode, img.size, img.getpixel((0, 0)))
        diff = ImageChops.difference(img, bg)
        
        # 找出非空白区域的边界框
        bbox = diff.getbbox()
        
        if bbox:
            print(f"Found non-empty area: {bbox}")
            # 添加边距
            bbox = (
                max(0, bbox[0] - add_border),
                max(0, bbox[1] - add_border),
                min(img.width, bbox[2] + add_border),
                min(img.height, bbox[3] + add_border)
            )
            print(f"Area with border: {bbox}")
            # 裁剪图片
            cropped = img.crop(bbox)
            # 保存裁剪后的图片
            cropped.save(output_path)
            print(f"Image cropped and saved: {output_path}")
            return True
        else:
            # 如果没有找到非空白区域，则保存原图
            img.save(output_path)
            print(f"No non-empty area found, saving original: {output_path}")
            return False
    except Exception as e:
        print(f"Error cropping image: {e}")
        return False

# Test the function with an existing image
trim_image("./image_reasoning_examples/output_normal/simple_question/8.png", "test_cropped.png", 10) 