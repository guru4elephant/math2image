from pdf2image import convert_from_path

# 将PDF转换为图片
images = convert_from_path('chinese_test.pdf', dpi=300)
images[0].save('chinese_test_image.png', 'PNG') 