# Math2Image

A tool for converting mathematical expressions and problem statements to images using LaTeX.

## Features

- Converts mathematical text in LaTeX format to high-quality images
- Supports intelligent text segmentation to preserve formula integrity
- Generates images in two modes:
  - Normal mode: Clean, typeset mathematical content
  - Real mode: Simulated handwritten appearance with various effects

## Requirements

- LaTeX installation (with XeTeX support)
- ImageMagick for image processing
- Python 3 with PIL/Pillow library for image cropping
- jq for JSON processing

## Usage

```bash
# Process a single problem
echo '{"problem": "Your math problem with $LaTeX$ here"}' | ./generate_images.sh

# Process multiple problems from a JSONL file
cat your_problems.jsonl | ./generate_images.sh

# Process a specific number of problems
head -n 20 your_problems.jsonl | ./generate_images.sh
```

## Output

- Images are saved in two directories:
  - `output_normal/simple_question/`: Clean typeset images
  - `output_real/simple_question/`: Simulated handwritten images
- Metadata is saved in:
  - `output_normal_data.jsonl`: Normal mode image data
  - `output_real_data.jsonl`: Real mode image data

## Example

Input:
```
{"problem": "What is the units digit of $31^3+13^3$?"}
```

Output:
- Normal mode image: `output_normal/simple_question/N.png`
- Real mode image: `output_real/simple_question/N.png`
