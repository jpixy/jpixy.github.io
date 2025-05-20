import os
from pathlib import Path

def generate_sidebar():
    articles_dir = Path("articles")
    sidebar_path = Path("_sidebar.md")
    
    if not articles_dir.exists():
        print(f"Error: Directory '{articles_dir}' not found.")
        return
    
    sidebar_content = ["<!-- 侧边栏 docs/_sidebar.md -->\n", "- Articles\n"]
    
    # 遍历articles下的所有子目录
    for category in sorted(os.listdir(articles_dir)):
        category_path = articles_dir / category
        if category_path.is_dir():
            sidebar_content.append(f"  - [{category}]\n")
            
            # 遍历子目录下的所有.md文件
            for md_file in sorted(category_path.glob("*.md")):
                # 获取不带扩展名的文件名
                title = md_file.stem
                # 构建相对路径
                rel_path = md_file.relative_to(articles_dir.parent)
                sidebar_content.append(f"    - [{title}](/{rel_path})\n")
    
    # 写入_sidebar.md文件
    with open(sidebar_path, "w", encoding="utf-8") as f:
        f.writelines(sidebar_content)
    
    print(f"Successfully generated {sidebar_path}")

if __name__ == "__main__":
    generate_sidebar()
