# Johnny's Tech Blog

A personal tech blog built with [Zola](https://www.getzola.org/) - a fast static site generator written in Rust.

## Quick Start

### Prerequisites

- [Zola](https://www.getzola.org/documentation/getting-started/installation/) (v0.17+)
- Git

### Local Development

```bash
# Clone the repository
git clone https://github.com/jpixy/jpixy.github.io.git
cd jpixy.github.io

# Start local development server
make serve

# Or manually:
zola serve
```

Visit `http://127.0.0.1:1111` to preview the site.

## Project Structure

```
.
├── config.toml          # Zola configuration
├── content/             # Markdown content
│   ├── _index.md        # Homepage content
│   ├── articles/        # Blog articles
│   │   ├── _index.md    # Articles section index
│   │   ├── ai/          # AI category
│   │   ├── python/      # Python category
│   │   └── ...          # Other categories
│   ├── resume/          # Resume page
│   └── wechat.md        # WeChat page
├── static/              # Static assets (CSS, images, JS)
├── templates/           # HTML templates
├── public/              # Generated site (git ignored)
└── Makefile             # Build commands
```

## Adding New Content

### Add a New Article

1. Navigate to the appropriate category folder under `content/articles/`
2. Create a new Markdown file with a descriptive name:

```bash
# Example: Add a new Python article
touch content/articles/python/py-my-new-article.md
```

3. Add frontmatter at the top of the file:

```markdown
+++
title = "My New Article Title"
date = 2024-01-15
description = "A brief description of the article"
[taxonomies]
tags = ["python", "tutorial"]
+++

# My New Article Title

Your content here...
```

4. Build and preview:

```bash
make serve
```

### Add a New Category

1. Create a new folder under `content/articles/`:

```bash
mkdir content/articles/newcategory
```

2. Create an `_index.md` file in the new folder:

```bash
cat > content/articles/newcategory/_index.md << 'EOF'
+++
title = "New Category"
sort_by = "title"
transparent = true
+++
EOF
```

3. Add articles to the new category following the article creation steps above.

## Important Notes

### Frontmatter Requirements

Every Markdown file **must** have TOML frontmatter:

```markdown
+++
title = "Article Title"    # Required
date = 2024-01-15          # Optional but recommended
description = "..."        # Optional
+++
```

### File Naming Conventions

- Use lowercase with hyphens: `my-article-name.md`
- Prefix with category abbreviation: `py-`, `k8s-`, `cpp-`, etc.
- Avoid special characters and spaces

### Code Blocks

Use standard language identifiers for syntax highlighting:

```markdown
```python
print("Hello World")
```

```bash
echo "Hello World"
```
```

**Avoid** using `plain` or `shell` - use `text` or `bash` instead.

### Images

1. Place images in `static/images/`
2. Reference them in Markdown:

```markdown
![Alt text](/images/my-image.png)
```

### Internal Links

Use Zola's internal link syntax:

```markdown
[Link Text](@/articles/python/py-my-article.md)
```

## Commands

### Using Make (Recommended)

```bash
make serve      # Start development server
make build      # Build for production
make clean      # Remove generated files
make check      # Check for broken links
make deploy     # Build and prepare for deployment
```

### Using Zola Directly

```bash
zola serve                    # Development server
zola build                    # Production build
zola check                    # Check links
zola build --base-url "/"     # Build with custom base URL
```

## Deployment

### Automatic (GitHub Actions)

Every push to the `main` branch automatically triggers a build and deployment to GitHub Pages.

### Manual

```bash
# Build the site
make build

# The generated site is in the public/ folder
# Push the public/ folder to your hosting provider
```

## Configuration

Edit `config.toml` to modify:

- `base_url`: Your site's URL
- `title`: Site title
- `description`: Site description
- `[extra]`: Custom variables (author, GitHub link, etc.)

## Troubleshooting

### Common Issues

1. **Styles not loading locally**: Hard refresh with `Ctrl+Shift+R`

2. **Build warnings about highlight languages**: Replace `plain` with `text`, `shell` with `bash`

3. **Broken anchor links**: Zola generates different anchor IDs than other tools. Check the generated HTML for correct anchor IDs.

4. **Search not working**: Ensure `build_search_index = true` in config.toml

### Getting Help

- [Zola Documentation](https://www.getzola.org/documentation/)
- [Zola GitHub Issues](https://github.com/getzola/zola/issues)

## License

Content is copyright Johnny. Code is MIT licensed.
