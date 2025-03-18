#!/bin/bash

# generate_images.sh - Convert JSONL problems to images in normal and real modes
# Usage: cat input.jsonl | ./generate_images.sh

# Ensure jq is installed
if ! command -v jq &> /dev/null; then
    echo "Error: This script requires jq. Please install it."
    echo "macOS: brew install jq"
    echo "Ubuntu/Debian: apt-get install jq"
    exit 1
fi

# Set UTF-8 locale
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8

# Path to the latex_to_image.py script
SCRIPT_PATH="../math2image/latex_to_image.py"

# Ensure the output directories exist
mkdir -p output_normal/simple_question output_real/simple_question

# For output jsonl files
NORMAL_JSONL="output_normal_data.jsonl"
REAL_JSONL="output_real_data.jsonl"

# Initialize empty JSONL files
> "$NORMAL_JSONL"
> "$REAL_JSONL"

# Calculate appropriate line length for images
# Using wider size to ensure all text fits properly
MAX_CHARS_PER_LINE=200  # Allow more characters per line (previously was around 44)
BORDER_SIZE=1         # Add generous border to ensure text doesn't get cut off

# Counter for generated images
counter=1

# Function to detect and extract math expressions
extract_math_expressions() {
    local text="$1"
    local expressions=()
    local in_math=false
    local current_expr=""
    local result=""
    local i=0
    
    # Read the text character by character
    while [ $i -lt ${#text} ]; do
        char="${text:$i:1}"
        next_char="${text:$i+1:1}"
        
        # If we encounter a $ and not in math mode, start math mode
        if [ "$char" = "$" ] && [ "$in_math" = false ]; then
            in_math=true
            current_expr="$"
        # If we encounter a $ and in math mode, end math mode
        elif [ "$char" = "$" ] && [ "$in_math" = true ]; then
            current_expr="$current_expr$"
            expressions+=("$current_expr")
            result="${result}MATH_PLACEHOLDER_${#expressions[@]}"
            in_math=false
            current_expr=""
        # If in math mode, add to current expression
        elif [ "$in_math" = true ]; then
            current_expr="$current_expr$char"
        # Otherwise, add to result
        else
            result="$result$char"
        fi
        ((i++))
    done
    
    # Print result and expressions for the caller to use
    echo "RESULT:$result"
    for expr in "${expressions[@]}"; do
        echo "EXPR:$expr"
    done
}

# Function to process the problem text and prepare it for LaTeX rendering
# Ensures that formulas are not wrapped across lines
prepare_problem_text() {
    local problem="$1"
    local max_chars_per_line="$2"
    
    # Extract math expressions and wrap text
    local extraction_result=$(extract_math_expressions "$problem")
    local wrapped_text=""
    local placeholder_text=""
    
    # Get the placeholder text (with MATH_PLACEHOLDER_X)
    placeholder_text=$(echo "$extraction_result" | grep "^RESULT:" | sed 's/^RESULT://')
    
    # Create a temporary file to apply word wrapping
    temp_wrap_file=$(mktemp)
    echo "$placeholder_text" > "$temp_wrap_file"
    
    # Use fmt to wrap text at word boundaries with specified width
    # fmt is better than fold for preserving word boundaries
    wrapped_text=$(fmt -w "$max_chars_per_line" "$temp_wrap_file")
    rm -f "$temp_wrap_file"
    
    # Extract the math expressions
    local expressions=()
    while IFS= read -r line; do
        if [[ "$line" == EXPR:* ]]; then
            expressions+=("${line#EXPR:}")
        fi
    done <<< "$extraction_result"
    
    # Replace placeholders with actual math expressions
    local i=1
    for expr in "${expressions[@]}"; do
        wrapped_text=$(echo "$wrapped_text" | sed "s/MATH_PLACEHOLDER_$i/$expr/g")
        ((i++))
    done
    
    # Return the processed text
    echo "$wrapped_text"
}

# Read each line from standard input
while IFS= read -r line; do
    # Skip empty lines
    [ -z "$line" ] && continue
    
    # Extract the problem field using jq
    problem=$(echo "$line" | jq -r '.problem')
    
    # Try to extract answer if available, otherwise leave empty
    answer=$(echo "$line" | jq -r '.answer // ""')
    
    # Skip if problem extraction failed or is empty
    if [ -z "$problem" ] || [ "$problem" = "null" ]; then
        echo "Warning: Skipping line $counter - could not extract problem field"
        continue
    fi
    
    echo "Processing problem $counter:"
    # Only show the first 80 characters of the problem to avoid potential encoding issues
    echo "${problem:0:80}..."
    
    # Generate filenames
    normal_filename="simple_question/${counter}.png"
    real_filename="simple_question/${counter}.png"
    
    # Create temporary problem files with proper word wrapping
    normal_problem_file=$(mktemp)
    prepare_problem_text "$problem" "$MAX_CHARS_PER_LINE" > "$normal_problem_file"
    
    # Normal mode - standard image with increased border to ensure all text fits
    echo "Generating normal mode image..."
    python "$SCRIPT_PATH" -i "$(cat "$normal_problem_file")" \
        -o "output_normal/${normal_filename}" \
        --dpi 100 \
        --max-chars-per-line "$MAX_CHARS_PER_LINE" \
        --border "$BORDER_SIZE" ||  echo "Normal mode generation failed"
#        --no-trim || echo "Normal mode generation failed"
    
    # Real mode - with random effects but still ensuring text fits
    echo "Generating real mode image..."
    
    # Create temporary problem file for real mode with slightly larger line width
    # to accommodate the random effects
    real_problem_file=$(mktemp)
    real_max_chars=$((MAX_CHARS_PER_LINE - 10))  # Slightly reduced to account for effects
    prepare_problem_text "$problem" "$real_max_chars" > "$real_problem_file"
    
    # Randomly choose 2-3 effects
    effects=()
    
    # Define all possible effects
    all_effects=(
        "--handwriting" 
        "--add-texture" 
        "--random-rotate" 
        "--add-noise" 
        "--add-blur"
    )
    
    # Randomly select how many effects to use (2 or 3)
    num_effects=$((2 + RANDOM % 2))
    
    # Shuffle the effects array (Fisher-Yates shuffle)
    for i in "${!all_effects[@]}"; do
        j=$((RANDOM % (i + 1)))
        temp="${all_effects[i]}"
        all_effects[i]="${all_effects[j]}"
        all_effects[j]="$temp"
    done
    
    # Take the first num_effects elements
    for ((i=0; i<num_effects; i++)); do
        effects+=("${all_effects[i]}")
    done
    
    echo "Using effects: ${effects[*]}"
    
    # Build and execute the command with larger border and explicit max chars per line
    python "$SCRIPT_PATH" -i "$(cat "$real_problem_file")" \
        -o "output_real/${real_filename}" \
        --dpi 100 \
        --max-chars-per-line "$real_max_chars" \
        --border "$(($BORDER_SIZE + 10))" \
        "${effects[@]}" || echo "Real mode generation failed"
    
    # Clean up
    rm -f "$normal_problem_file" "$real_problem_file"
    
    # Create a temp file containing the complete prompt text
    prompt_file=$(mktemp)
    cat > "$prompt_file" << 'EOT'
<image>You are a programming expert in Python, specializing in solving mathematical problems with efficient and concise code. 
Before generating the code, you need to engage in deep thinking, analyze the essence of the problem, and determine the optimal solution. 

EOT
    
    # Append problem to prompt file
    echo "$problem" >> "$prompt_file"
    
    # Create JSON objects using jq
    normal_json=$(jq -c -n \
        --arg id "$counter" \
        --arg image "$normal_filename" \
        --rawfile prompt "$prompt_file" \
        --arg answer "$answer" \
        '{
            id: ($id|tonumber), 
            image: $image, 
            conversations: [
                {
                    from: "human", 
                    value: $prompt
                }, 
                {
                    from: "gpt", 
                    value: $answer
                }
            ]
        }')
    
    real_json=$(jq -c -n \
        --arg id "$counter" \
        --arg image "$real_filename" \
        --rawfile prompt "$prompt_file" \
        --arg answer "$answer" \
        '{
            id: ($id|tonumber), 
            image: $image, 
            conversations: [
                {
                    from: "human", 
                    value: $prompt
                }, 
                {
                    from: "gpt", 
                    value: $answer
                }
            ]
        }')
    
    # Append to JSONL files
    echo "$normal_json" >> "$NORMAL_JSONL"
    echo "$real_json" >> "$REAL_JSONL"
    
    # Clean up temp files
    rm -f "$prompt_file"
    
    echo "Completed processing problem $counter"
    echo "-----------------------"
    
    # Increment counter
    ((counter++))
done

echo "All processing complete. Generated $(($counter - 1)) images in each mode."
echo "Normal mode images are in: output_normal/simple_question/"
echo "Real mode images are in: output_real/simple_question/"
echo "Normal mode data: $NORMAL_JSONL"
echo "Real mode data: $REAL_JSONL" 
