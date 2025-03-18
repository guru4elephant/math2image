# Image Reasoning Examples

这个目录包含用于生成数学问题图像的脚本，支持将LaTeX格式的数学问题文本转换为图像，用于各种应用场景。

## 功能特点

- 从JSONL文件中提取数学问题文本
- 支持两种图像生成模式：
  - **标准模式**：生成标准448x448像素的图像，不添加特效
  - **真实模式**：随机应用2-3种特效（手写体、纸张纹理、随机旋转、噪点、模糊）

## 使用方法

### 准备工作

1. 确保已安装依赖：
   ```bash
   # 安装jq工具（用于解析JSON）
   brew install jq  # macOS
   apt-get install jq  # Ubuntu/Debian
   ```

2. 确保父目录中的`math2image`项目已正确安装

### 准备输入数据

创建JSONL格式的输入文件，每行包含一个JSON对象，必须有`problem`字段，例如：

```json
{"id": "problem1", "problem": "求函数 $f(x) = x^2 + 2x + 1$ 的最小值。"}
{"id": "problem2", "problem": "计算积分 $\\int_{0}^{1} x^2 \\, dx$。"}
```

### 运行脚本

使用管道从文件输入：

```bash
cat sample_problems.jsonl | ./generate_images.sh
```

或者直接将JSONL文件作为输入：

```bash
./generate_images.sh < sample_problems.jsonl
```

### 输出

脚本将在以下目录生成图像：

- `output_normal/` - 标准模式生成的图像
- `output_real/` - 真实模式生成的图像

图像按照处理顺序编号，例如：`problem_1.png`, `problem_2.png`等。

## 自定义脚本

可以修改脚本中的以下参数来自定义输出：

- `CHARS_PER_LINE` - 每行的字符数（默认为40，适合448px宽度）
- `all_effects` - 可用特效列表
- 调整随机图像大小的范围（目前为400-600px）

## 示例

提供了示例JSONL文件`sample_problems.jsonl`，包含5个数学问题样例。运行以下命令测试：

```bash
./generate_images.sh < sample_problems.jsonl
``` 