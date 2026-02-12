#!/usr/bin/env python3
"""Reorganize ai-34 article: move 追问 sections to end of each chapter."""
import re

INPUT = "content/articles/ai/ai-34-从模型诞生到AI应用全链路认知.md"

with open(INPUT, "r") as f:
    lines = f.readlines()

content = "".join(lines)

# --- Helper: split content into chapters by ## headings ---
# We'll work with the raw text and do targeted replacements.

# Difficulty labels for each 追问 title (substring match)
DIFFICULTY = {
    "什么是激活函数": "[基础]",
    "为什么模型需要那么多层": "[基础]",
    "为什么计算图是": "[进阶]",
    "为什么参数初始化": "[进阶]",
    "Token 是什么": "[基础]",
    "为什么 LLM 的训练目标": "[基础]",
    "为什么需要「损失函数」": "[基础]",
    "反向传播怎么工作": "[基础]",
    "「学习率」是什么": "[进阶]",
    "梯度下降会不会": "[进阶]",
    "为什么训练一定要用 GPU": "[进阶]",
    "怎么知道模型训练": "[前沿]",
    "为什么 LLM 生成文本": "[基础]",
    "为什么 LLM 会「胡说八道」": "[基础]",
    "LLM 每步输出一个概率分布": "[进阶]",
    "70B 参数的模型有多大": "[进阶]",
    "嵌入模型怎么做到": "[进阶]",
    "为什么 Transformer 取代": "[进阶]",
    "为什么需要导出到 ONNX": "[进阶]",
    "「涌现」是什么原理": "[前沿]",
    "什么时候用 Prompt": "[进阶]",
    "为什么 LLM 改 prompt": "[进阶]",
    "堆参数": "[前沿]",
    "模型为什么不能把训练数据": "[进阶]",
}

def get_difficulty(title):
    for key, label in DIFFICULTY.items():
        if key in title:
            return label
    return "[进阶]"

DEEP_DIVE_INTRO = """> 以下追问按难度分层标注：**[基础]** 适合所有读者；**[进阶]** 适合想深入理解原理的读者；**[前沿]** 适合对前沿研究感兴趣的读者。主线阅读可跳过本节，需要时再回来查阅。

"""

# Parse the file line by line into a structure
# We need to identify:
# 1. All "#### 追问:" or "#### 追问：" sections 
# 2. The "**追问：" inline bold headings (line 228 in original)
# 3. Group them by chapter

# Strategy: Process each chapter block separately
# Split by "## " at the start of lines (level 2 headings = chapters)

def split_into_chunks(text):
    """Split text by ## headings, keeping the heading with the chunk."""
    chunks = []
    current = []
    for line in text.split('\n'):
        if line.startswith('## ') and current:
            chunks.append('\n'.join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        chunks.append('\n'.join(current))
    return chunks

chunks = split_into_chunks(content)

def process_chapter(chunk, chapter_label, next_section_num):
    """
    Extract #### 追问 sections from the chunk, move them to a new
    "### X.N 深度追问" section at the end (before ---)
    """
    lines = chunk.split('\n')
    
    # Find all #### 追问 sections
    main_lines = []
    zhuiwen_sections = []  # list of (title, content_lines)
    
    i = 0
    in_zhuiwen = False
    current_zw_title = ""
    current_zw_lines = []
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this is a #### 追问 heading
        if line.startswith('#### 追问：') or line.startswith('#### 追问:'):
            # Save any previous 追问
            if in_zhuiwen and current_zw_lines:
                zhuiwen_sections.append((current_zw_title, current_zw_lines))
            
            # Start new 追问
            in_zhuiwen = True
            # Extract title after "追问："
            title = line.replace('#### 追问：', '').replace('#### 追问:', '').strip()
            current_zw_title = title
            current_zw_lines = []
            i += 1
            continue
        
        # Check if we hit a ### heading (end of current 追问 if we're in one)
        if line.startswith('### ') and in_zhuiwen:
            # Save the 追问
            zhuiwen_sections.append((current_zw_title, current_zw_lines))
            in_zhuiwen = False
            current_zw_title = ""
            current_zw_lines = []
            main_lines.append(line)
            i += 1
            continue
        
        # Check if we hit a ## heading (chapter boundary)
        if line.startswith('## ') and i > 0 and in_zhuiwen:
            zhuiwen_sections.append((current_zw_title, current_zw_lines))
            in_zhuiwen = False
            main_lines.append(line)
            i += 1
            continue
        
        if in_zhuiwen:
            current_zw_lines.append(line)
        else:
            main_lines.append(line)
        
        i += 1
    
    # Handle last 追问 if file ends in one
    if in_zhuiwen and current_zw_lines:
        zhuiwen_sections.append((current_zw_title, current_zw_lines))
    
    if not zhuiwen_sections:
        return chunk  # No 追问 to move
    
    # Now reconstruct: main content + 深度追问 section
    # Find where to insert the 深度追问 (before the last --- if present)
    main_text = '\n'.join(main_lines)
    
    # Build the 深度追问 section
    deep_dive = f"\n### {chapter_label}.{next_section_num} 深度追问\n\n"
    deep_dive += DEEP_DIVE_INTRO
    
    for title, content_lines in zhuiwen_sections:
        difficulty = get_difficulty(title)
        deep_dive += f"#### {difficulty} {title}\n\n"
        # Add content, stripping leading/trailing blank lines
        content_text = '\n'.join(content_lines).strip()
        deep_dive += content_text + "\n\n"
    
    # Insert before the final ---
    if main_text.rstrip().endswith('---'):
        # Remove the trailing --- and add our section before it
        main_text = main_text.rstrip()
        main_text = main_text[:-3].rstrip()
        result = main_text + "\n\n" + deep_dive + "\n---"
    else:
        result = main_text + "\n\n" + deep_dive
    
    return result

# Process each chunk
new_chunks = []
for chunk in chunks:
    first_line = chunk.split('\n')[0]
    
    if first_line.startswith('## I. What is a Model?'):
        new_chunks.append(process_chapter(chunk, "1", 4))
    elif first_line.startswith('## II. How is a Model Born?'):
        new_chunks.append(process_chapter(chunk, "2", 4))
    elif first_line.startswith('## III. How is a Model Used?'):
        new_chunks.append(process_chapter(chunk, "3", 4))
    elif first_line.startswith('## IV. Why RAG'):
        new_chunks.append(process_chapter(chunk, "4", 4))
    elif first_line.startswith('## V. End-to-End'):
        new_chunks.append(process_chapter(chunk, "5", 7))
    elif first_line.startswith('## VII. LLM vs'):
        new_chunks.append(process_chapter(chunk, "7", 5))
    else:
        new_chunks.append(chunk)

result = '\n'.join(new_chunks)

# Fix double blank lines that might have been introduced
while '\n\n\n\n' in result:
    result = result.replace('\n\n\n\n', '\n\n\n')

# Update Overview table references
overview_replacements = [
    ('I (1.2 追问)', 'I (1.4)'),
    ('II (2.1 追问)', 'II (2.4)'),
    ('II (2.2 追问)', 'II (2.4)'),
    ('III (3.2 追问)', 'III (3.4)'),
    ('III (3.3 追问)', 'III (3.4)'),
    ('IV (4.3 追问)', 'IV (4.4)'),
    ('V (5.2 追问)', 'V (5.7)'),
    ('V (5.3 追问)', 'V (5.7)'),
    ('VII (7.2 追问)', 'VII (7.5)'),
    ('VII (7.3 追问)', 'VII (7.5)'),
    ('VII (7.4 追问)', 'VII (7.5)'),
]
for old, new in overview_replacements:
    result = result.replace(old, new)

with open(INPUT, "w") as f:
    f.write(result)

print("Done. Reorganization complete.")
print("Chapters with 追问 moved to 深度追问:")
for chunk in new_chunks:
    first_line = chunk.split('\n')[0]
    if '深度追问' in chunk:
        count = chunk.count('#### [')
        print(f"  {first_line[:50]}... → {count} 追问")
