# SeaweedFS Node Templates

This directory contains Jinja2 templates for generating SeaweedFS node detail pages.

## Structure

- `base_node.html` - Base template with common HTML structure and CSS
- `generate_templates.py` - Python script to render templates

## Usage

### Generate All Templates

```bash
python3 generate_templates.py
```

This will generate HTML files for:
- Filers (filer1.html, filer2.html) - Combined filer and S3 functionality
- Volumes (volume1.html, volume2.html, volume3.html)
- Masters (master1.html, master2.html, master3.html)

### Template Variables

Each node type supports the following variables:

- `page_title` - Browser tab title
- `node_title` - Main heading
- `node_type` - Type of node (e.g., "Filer & S3 Node")
- `node_description` - Description text
- `status_items` - Dictionary of status information
- `connected_components` - List of connected components
- `storage_stats` - Storage-related statistics
- `s3_stats` - S3-specific statistics (for filers)
- `operations` - Operation counters
- `api_links` - Direct API access links
- `custom_js` - Custom JavaScript for the node type

## Benefits

1. **DRY Principle** - Single source of truth for HTML structure
2. **Maintainability** - Changes to common elements only need to be made once
3. **Consistency** - All pages have the same look and feel
4. **Flexibility** - Easy to add new node types or modify existing ones
5. **Automation** - Templates can be regenerated programmatically

## Docker Integration

The templates are now integrated with Docker for automated rendering:

### Production Build (Recommended)

```bash
# Build nginx image with templates rendered at build time
./build_nginx.sh

# Or manually:
docker-compose build nginx
docker-compose up -d nginx
```

### Development Build (Alternative)

```bash
# Use startup-rendering version
sed -i 's/Dockerfile.nginx/Dockerfile.nginx-startup/' docker-compose.yml
docker-compose build nginx
docker-compose up -d nginx
```

### Docker Benefits

1. **Security**: No Python runtime in production container
2. **Performance**: Templates rendered once at build time
3. **Reliability**: No runtime dependencies for template rendering
4. **Consistency**: Template changes require rebuild, ensuring all instances are updated

### Template Updates in Docker

When you modify templates or the generator:

```bash
# Rebuild the nginx image
docker-compose build --no-cache nginx
docker-compose up -d nginx
```

## Adding New Node Types

1. Add a new render method in `NodeTemplateRenderer` class
2. Define the template variables for the new node type
3. Add the generation call in `generate_all_templates()`
4. Update nginx configuration if needed
5. Rebuild the Docker image

## Customization

To modify the appearance or functionality:

1. Edit `base_node.html` for common changes
2. Modify the data dictionaries in `generate_templates.py` for node-specific changes
3. Update the `custom_js` for node-specific JavaScript behavior
4. Rebuild Docker image for production deployment
