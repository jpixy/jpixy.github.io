#!/usr/bin/env python3
"""
Script to fix Chinese parentheses in Mermaid code blocks.
Replaces Chinese () with spaces in Mermaid blocks only.
"""

import re
import os

BASE_PATH = "content/articles/quant"

FILES_TO_FIX = [
    "quant-03-中国大陆量化交易接口与数据.md",
    "quant-08-回测系统设计与实现.md",
    "quant-10-因子研究方法论.md",
    "quant-11-加密货币量化.md",
    "quant-12-期权量化入门.md",
    "quant-15-外汇量化入门.md",
    "quant-16-市场微结构.md",
    "quant-17-事件驱动策略.md",
    "quant-18-个人自动化量化交易入门.md",
    "quant-19-CTP期货开户与期货公司选择.md",
    "quant-22-Cpp个人量化交易实战.md",
    "quant-24-A股程序化交易接口QMT与Ptrade.md",
]


def fix_chinese_parens(content):
    """Replace Chinese parentheses with spaces in mermaid blocks only"""
    lines = content.split('\n')
    in_mermaid = False
    result = []
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```mermaid"):
            in_mermaid = True
            result.append(line)
        elif stripped.startswith("```") and in_mermaid:
            in_mermaid = False
            result.append(line)
        elif in_mermaid:
            # Replace Chinese parentheses in mermaid blocks
            new_line = re.sub(r'（([^）]+)）', r' \1', line)
            result.append(new_line)
        else:
            result.append(line)
    
    return '\n'.join(result)


def main():
    for fname in FILES_TO_FIX:
        fpath = os.path.join(BASE_PATH, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content = fix_chinese_parens(content)
            
            if content != new_content:
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Fixed: {fname}")
            else:
                print(f"No changes needed: {fname}")
        except Exception as e:
            print(f"Error processing {fname}: {e}")

    print("\nDone!")


if __name__ == "__main__":
    main()
