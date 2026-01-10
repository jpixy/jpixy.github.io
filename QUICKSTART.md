# Quick Start Guide

## 本地预览

```bash
make serve
# 访问 http://127.0.0.1:1111
```

---

## 添加新文章

### 方法一：使用 Make 命令（推荐）

```bash
make new-article
# 按提示输入：分类、文件名、标题
```

### 方法二：手动创建

1. 在 `content/articles/<分类>/` 下创建 `.md` 文件：

```bash
touch content/articles/python/py-my-new-article.md
```

2. 添加以下内容：

```markdown
+++
title = "文章标题"
date = 2024-01-15
+++

# 文章标题

正文内容...
```

---

## 添加新目录（分类）

### 方法一：使用 Make 命令（推荐）

```bash
make new-category
# 按提示输入：目录名、显示标题
```

### 方法二：手动创建

```bash
# 1. 创建目录
mkdir content/articles/newcategory

# 2. 创建 _index.md
cat > content/articles/newcategory/_index.md << 'EOF'
+++
title = "New Category"
sort_by = "title"
transparent = true
+++
EOF
```

---

## 发布

### 自动发布（推荐）

直接推送到 GitHub，自动部署：

```bash
git add .
git commit -m "Add new article"
git push
```

### 手动构建

```bash
make build
# 输出在 public/ 目录
```

---

## 常用命令

| 命令 | 说明 |
|------|------|
| `make serve` | 本地预览 |
| `make build` | 构建网站 |
| `make new-article` | 添加文章 |
| `make new-category` | 添加目录 |
| `make stats` | 查看统计 |
| `make clean` | 清理构建 |

---

## 注意事项

1. **文件必须有 frontmatter**：
   ```markdown
   +++
   title = "标题"
   +++
   ```

2. **代码块使用标准语言**：
   - ✅ `python`, `bash`, `go`, `rust`, `yaml`, `json`
   - ❌ `plain`, `shell`（用 `text` 或 `bash` 替代）

3. **图片放在 `static/images/`**，引用时用 `/images/xxx.png`

4. **内部链接格式**：`[链接文字](@/articles/python/py-xxx.md)`
