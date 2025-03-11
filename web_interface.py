import os
import uuid
from flask import Flask, render_template, request, jsonify, send_file
from latex_to_image import render_latex_to_image, list_available_fonts

app = Flask(__name__)

# 设置上传文件夹路径
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'images')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 设置允许上传的文件类型
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

@app.route('/')
def index():
    # 获取可用字体列表
    available_fonts = list_available_fonts()
    return render_template('index.html', available_fonts=available_fonts)

@app.route('/render', methods=['POST'])
def render_latex():
    try:
        # 获取请求中的参数
        if 'json' in request.content_type.lower():
            data = request.json
            latex_text = data.get('latex', '')
            border = int(data.get('border', 10))
            use_xelatex = data.get('use_xelatex', True)
            max_chars_per_line = -1
            dpi = 300
            auto_trim = True
            font = 'PingFang SC'
            font_size = None
            random_font = False
            rotate = 0
            random_rotate = False
            bg_color = 'white'
            random_bg = False
            add_noise = False
            add_blur = False
            add_texture = False
            add_lighting = False
            no_effects = False
            noise_intensity = 0.05
            blur_radius = 0.5
            texture_intensity = 0.1
            lighting_intensity = 0.1
            handwriting = False
            handwriting_intensity = 0.5
        else:
            # 从表单中获取LaTeX文本
            latex_text = request.form.get('latex', '')
            if not latex_text:
                return jsonify({'error': '请输入LaTeX内容'}), 400
                
            # 获取其他基本选项
            border = int(request.form.get('border', 10))
            dpi = int(request.form.get('dpi', 300))
            auto_trim = request.form.get('auto_trim') == 'true'
            font = request.form.get('font', 'PingFang SC')
            font_size = request.form.get('font_size', '')
            random_font = request.form.get('random_font') == 'true'
            use_xelatex = True
            
            # 获取高级选项
            try:
                max_chars_per_line_str = request.form.get('max_chars_per_line', '-1')
                max_chars_per_line = int(max_chars_per_line_str) if max_chars_per_line_str.strip() else -1
            except ValueError:
                max_chars_per_line = -1
                print(f"警告: 无效的每行字符数设置: {request.form.get('max_chars_per_line')}, 默认为不限制")
                
            rotate = float(request.form.get('rotate', 0))
            random_rotate = request.form.get('random_rotate') == 'true'
            bg_color = request.form.get('bg_color', 'white')
            random_bg = request.form.get('random_bg') == 'true'
            
            # 获取特效选项
            add_noise = request.form.get('add_noise') == 'true'
            add_blur = request.form.get('add_blur') == 'true'
            add_texture = request.form.get('add_texture') == 'true'
            add_lighting = request.form.get('add_lighting') == 'true'
            no_effects = request.form.get('no_effects') == 'true'
            
            # 特效强度
            noise_intensity = float(request.form.get('noise_intensity', 0.05))
            blur_radius = float(request.form.get('blur_radius', 0.5))
            texture_intensity = float(request.form.get('texture_intensity', 0.1))
            lighting_intensity = float(request.form.get('lighting_intensity', 0.1))
            
            # 手写体选项
            handwriting = request.form.get('handwriting') == 'true'
            try:
                handwriting_intensity = float(request.form.get('handwriting_intensity', 0.5))
                handwriting_intensity = max(0.0, min(1.0, handwriting_intensity))  # 限制在0.0-1.0之间
            except ValueError:
                handwriting_intensity = 0.5

        # 生成一个唯一的输出文件名
        output_filename = f"{uuid.uuid4()}.png"
        output_path = os.path.join(UPLOAD_FOLDER, output_filename)
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 配置图像效果
        effects = {}
        if add_noise:
            effects['noise'] = noise_intensity
        if add_blur:
            effects['blur'] = blur_radius
        if add_texture:
            effects['texture'] = texture_intensity
        if add_lighting:
            effects['lighting'] = lighting_intensity
        
        # 输出调试信息
        print(f"渲染设置: max_chars_per_line={max_chars_per_line}, 类型={type(max_chars_per_line)}")
        if handwriting:
            print(f"启用手写体效果，强度: {handwriting_intensity}")
        
        # 渲染LaTeX为图片
        render_latex_to_image(
            latex_text, 
            output_path=output_path, 
            dpi=dpi,
            auto_trim=auto_trim,
            border=border,
            use_xelatex=use_xelatex,
            main_font=font,
            font_size=font_size,
            random_font=random_font,
            rotate_angle=rotate,
            random_rotate=random_rotate,
            bg_color=bg_color,
            random_bg_color=random_bg,
            effects=effects,
            apply_effects=not no_effects,
            max_chars_per_line=max_chars_per_line,
            handwriting=handwriting,
            handwriting_intensity=handwriting_intensity
        )
        
        image_url = f"/static/images/{output_filename}"
        
        return jsonify({
            'success': True,
            'image_url': image_url,
            'filename': output_filename
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'渲染失败: {str(e)}'}), 500

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename), 
                     mimetype='image/png',
                     as_attachment=True,
                     download_name=filename)

if __name__ == '__main__':
    app.run(debug=True, port=5001) 