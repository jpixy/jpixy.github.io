# Makefile for Johnny's Tech Blog (Zola)

.PHONY: help serve build clean check deploy new-article new-category

# Default target
help:
	@echo "Available commands:"
	@echo "  make serve         - Start local development server (http://127.0.0.1:1111)"
	@echo "  make build         - Build the site for production"
	@echo "  make clean         - Remove generated files"
	@echo "  make check         - Check for broken links"
	@echo "  make deploy        - Build and prepare for deployment"
	@echo "  make new-article   - Create a new article (interactive)"
	@echo "  make new-category  - Create a new category (interactive)"

# Start development server
serve:
	@echo "Starting Zola development server..."
	@echo "Visit http://127.0.0.1:1111"
	zola serve

# Build for production
build:
	@echo "Building site for production..."
	zola build
	@echo "Build complete! Output in ./public/"

# Clean generated files
clean:
	@echo "Cleaning generated files..."
	rm -rf public/
	@echo "Clean complete!"

# Check for broken links
check:
	@echo "Checking for broken links..."
	zola check

# Build and prepare for deployment
deploy: clean build
	@echo "Site ready for deployment in ./public/"

# Create a new article interactively
new-article:
	@echo "Creating a new article..."
	@read -p "Category (e.g., python, cloud, ai): " category; \
	read -p "Article slug (e.g., my-new-article): " slug; \
	read -p "Article title: " title; \
	filepath="content/articles/$$category/$$slug.md"; \
	if [ ! -d "content/articles/$$category" ]; then \
		echo "Error: Category '$$category' does not exist."; \
		echo "Run 'make new-category' first to create it."; \
		exit 1; \
	fi; \
	echo "+++" > $$filepath; \
	echo "title = \"$$title\"" >> $$filepath; \
	echo "date = $$(date +%Y-%m-%d)" >> $$filepath; \
	echo "description = \"\"" >> $$filepath; \
	echo "+++" >> $$filepath; \
	echo "" >> $$filepath; \
	echo "# $$title" >> $$filepath; \
	echo "" >> $$filepath; \
	echo "Your content here..." >> $$filepath; \
	echo "Created: $$filepath"

# Create a new category
new-category:
	@echo "Creating a new category..."
	@read -p "Category folder name (lowercase, e.g., golang): " folder; \
	read -p "Category display title (e.g., Go Language): " title; \
	mkdir -p "content/articles/$$folder"; \
	echo "+++" > "content/articles/$$folder/_index.md"; \
	echo "title = \"$$title\"" >> "content/articles/$$folder/_index.md"; \
	echo "sort_by = \"title\"" >> "content/articles/$$folder/_index.md"; \
	echo "transparent = true" >> "content/articles/$$folder/_index.md"; \
	echo "+++" >> "content/articles/$$folder/_index.md"; \
	echo "Created category: content/articles/$$folder/"

# Watch for changes and rebuild (alternative to serve)
watch:
	@echo "Watching for changes..."
	zola build && fswatch -o content templates static | xargs -n1 -I{} zola build

# Show site statistics
stats:
	@echo "Site Statistics:"
	@echo "================"
	@echo "Categories: $$(ls -d content/articles/*/ 2>/dev/null | wc -l)"
	@echo "Articles: $$(find content/articles -name "*.md" ! -name "_index.md" | wc -l)"
	@echo "Total Markdown files: $$(find content -name "*.md" | wc -l)"
	@if [ -d "public" ]; then \
		echo "Build size: $$(du -sh public | cut -f1)"; \
	fi
