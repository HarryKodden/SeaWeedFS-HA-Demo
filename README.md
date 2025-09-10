```markdown
# SeaweedFS High Availability Demo

A comprehensive Docker-based demonstration of a SeaweedFS distributed file system cluster with high availability, featuring an interactive web dashboard, REST API, and automated monitoring.

## 🚀 Features

### Core Components
- **3 Master Nodes**: Distributed metadata management with automatic failover
- **3 Volume Servers**: Data storage with configurable replication
- **2 Filer Servers**: File system interface with S3 API support
- **Nginx Proxy**: Load balancing and reverse proxy with authentication
- **REST API**: Full cluster management with FastAPI and interactive documentation
- **Web Dashboard**: Real-time monitoring and management interface

### Advanced Features
- **High Availability**: Automatic failover and load balancing
- **S3 Compatibility**: Full S3 API support for file operations
- **Interactive Documentation**: Swagger UI and ReDoc for API exploration
- **Health Monitoring**: Automated health checks for all services
- **Container Management**: Start/stop/restart services via API
- **Real-time Logs**: Live log streaming from all containers

## 📋 Prerequisites

- Docker and Docker Compose
- At least 4GB RAM available
- Linux/macOS/Windows with Docker support
- Basic understanding of distributed systems (optional)

## 🛠️ Quick Start

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd SeaWeedFS-HA-Demo
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your preferred settings
   ```

3. **Start the cluster:**
   ```bash
   docker-compose up -d
   ```

4. **Access the dashboard:**
   - Open http://localhost in your browser
   - Username: `admin`
   - Password: `seaweedadmin`

5. **Explore the API:**
   - Interactive docs: http://localhost/api/docs
   - API reference: http://localhost/api/redoc

## 📁 Project Structure

```
SeaweedFS-HA-Demo/
├── docker-compose.yml      # Service definitions with YAML anchors
├── .env                    # Environment configuration
├── proxy/
│   ├── nginx.conf          # Nginx configuration with routing rules
│   └── Dockerfile          # Nginx container setup
├── api/
│   ├── api.py              # FastAPI application with full documentation
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile          # API container setup
├── .htpasswd               # HTTP authentication credentials
└── README.md              # This file
```

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# Domain configuration
DOMAIN=example.com

# Docker group ID for API container socket access
DOCKER_GID=1001

# SeaweedFS URL endpoints (through nginx proxy)
SEAWEED_MASTER_URL=http://localhost/master/1
SEAWEED_VOLUME_URL=http://localhost/volume/1
SEAWEED_FILER_URL=http://localhost/filer/1
SEAWEED_S3_URL=http://localhost:8333

# Authentication for admin access
SEAWEED_AUTH_USER=admin
SEAWEED_AUTH_PASSWORD=seaweedadmin

# S3 API credentials
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

### Docker Compose Services

The `docker-compose.yml` uses YAML anchors for elegant service definitions:

- **Base Configurations**: Common settings defined once and reused
- **Service Inheritance**: Each service extends base configuration with overrides
- **Health Checks**: Automated monitoring for all services
- **Dependencies**: Proper startup order and health-based waiting

## 🌐 Web Interface

### Dashboard Features
- **Cluster Overview**: Visual representation of all nodes
- **Service Status**: Real-time health indicators
- **Node Details**: Individual service information and controls
- **API Links**: Direct access to interactive documentation
- **Log Viewer**: Live streaming of service logs

### API Documentation
- **Swagger UI** (`/api/docs`): Interactive API testing
- **ReDoc** (`/api/redoc`): Clean API reference documentation
- **Full CRUD Operations**: Complete cluster management via REST API

## 🔧 API Endpoints

### Container Management
```bash
# Get container status
GET /api/containers/{container_name}

# Get container health
GET /api/containers/{container_name}/health

# Start container
POST /api/containers/{container_name}

# Stop container
DELETE /api/containers/{container_name}

# List all containers
GET /api/containers
```

### S3 Operations
```bash
# Get S3 operations data
GET /s3-operations
```

### Health Check
```bash
# Service health
GET /api/health
```

## 📊 Monitoring & Logs

### Health Checks
All services include automated health checks:
- **Masters**: Cluster status endpoint
- **Volumes**: Volume status endpoint
- **Filers**: HTTP availability check
- **API**: Health endpoint response

### Log Access
```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f master1

# View API logs
docker-compose logs -f api
```

## 🔒 Security

### Authentication
- HTTP Basic Authentication for all admin interfaces
- Configurable credentials in `.htpasswd`
- Nginx-level authentication for all services

### Network Security
- Internal Docker network for service communication
- External access only through nginx proxy
- Port restrictions and firewall rules

## 🚀 Advanced Usage

### Scaling Services
```bash
# Add more volume servers
docker-compose up -d volume4

# Scale existing services
docker-compose up -d --scale volume=5
```

### Custom Configuration
```bash
# Modify service parameters
vim docker-compose.yml

# Rebuild and restart
docker-compose up -d --build
```

### Backup & Recovery
```bash
# Backup data volumes
docker run --rm -v seaweedfs_data:/data -v $(pwd):/backup alpine tar czf /backup/seaweedfs-backup.tar.gz -C /data .

# Restore from backup
docker run --rm -v seaweedfs_data:/data -v $(pwd):/backup alpine tar xzf /backup/seaweedfs-backup.tar.gz -C /data
```

## 🐛 Troubleshooting

### Common Issues

**Services not starting:**
```bash
# Check service status
docker-compose ps

# View service logs
docker-compose logs <service_name>

# Restart services
docker-compose restart
```

**API not responding:**
```bash
# Check API health
curl http://localhost/api/health

# View API logs
docker-compose logs api
```

**Dashboard not loading:**
```bash
# Check nginx status
docker-compose ps proxy

# View nginx logs
docker-compose logs proxy
```

**Authentication issues:**
```bash
# Verify .htpasswd file
cat .htpasswd

# Test authentication
curl -u admin:seaweedadmin http://localhost/api/health
```

### Performance Tuning

**Memory allocation:**
```yaml
# In docker-compose.yml
deploy:
  resources:
    limits:
      memory: 2G
    reservations:
      memory: 1G
```

**CPU limits:**
```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
```

**S3 Options**

The `AWS_S3_ADDRESSING_STYLE` environment variable controls how AWS CLI and SDKs construct S3 URLs. Here are the available variants:

## Available Variants:

### **1. `path` (Recommended for SeaWeedFS)**
- **URL Format:** `http://endpoint/bucket/key`
- **Example:** `http://localhost:8333/my-bucket/my-file.txt`
- **Compatibility:** Works with all bucket names, including those with dots
- **SeaWeedFS:** This is the default and recommended style for SeaWeedFS S3

### **2. `virtual`**
- **URL Format:** `http://bucket.endpoint/key`
- **Example:** `http://my-bucket.localhost:8333/my-file.txt`
- **Compatibility:** May not work with buckets containing dots or special characters
- **SeaWeedFS:** Supported but may cause issues with certain bucket names

### **3. `auto`**
- **URL Format:** Automatically chooses between `path` and `virtual`
- **Logic:** Uses `virtual` for simple bucket names, `path` for complex ones
- **Compatibility:** Best of both worlds, but less predictable
- **SeaWeedFS:** May work, but `path` is more reliable

## Recommended Configuration for SeaWeedFS:

```bash
# In your .env file
AWS_S3_ADDRESSING_STYLE=path
```

## Why `path` is Recommended:

- **SeaWeedFS Implementation:** Uses path-style addressing internally
- **Bucket Name Flexibility:** Works with any bucket name format
- **Consistency:** Matches how SeaWeedFS handles S3 requests
- **Compatibility:** Avoids issues with virtual hosting limitations

## Testing Different Styles:

You can test the addressing styles with your current setup:

```bash
# Test with path style (current)
AWS_S3_ADDRESSING_STYLE=path aws s3 ls s3://test-bucket --endpoint-url=http://localhost:8333

# Test with virtual style
AWS_S3_ADDRESSING_STYLE=virtual aws s3 ls s3://test-bucket --endpoint-url=http://localhost:8333

# Test with auto style
AWS_S3_ADDRESSING_STYLE=auto aws s3 ls s3://test-bucket --endpoint-url=http://localhost:8333
```

For SeaWeedFS, stick with `path` style for the most reliable operation! 🎯

**Note:** The addressing style affects how URLs are constructed but doesn't change the underlying S3 API functionality. SeaWeedFS handles both styles, but `path` is the most compatible.

## 📚 API Documentation

The API includes comprehensive documentation:

- **Interactive Testing**: Use Swagger UI to test endpoints directly
- **Response Examples**: All endpoints include sample requests/responses
- **Error Handling**: Detailed error codes and messages
- **Authentication**: Built-in auth testing in documentation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the Apache 2.0 License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [SeaweedFS](https://github.com/chrislusf/seaweedfs) - The distributed file system
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Docker](https://www.docker.com/) - Containerization platform
- [Nginx](https://nginx.org/) - High-performance web server

## 📞 Support

For issues and questions:
- Check the troubleshooting section above
- Review the API documentation
- Open an issue on GitHub
- Consult the SeaweedFS documentation

---

**Last updated:** September 10, 2025
**Version:** 1.0.0
```

## Key Updates Made:

### 1. **Comprehensive Feature Overview**
- Added detailed description of all components
- Highlighted advanced features like HA, S3 support, and monitoring
- Included interactive documentation features

### 2. **Updated Project Structure**
- Reflects the current file organization
- Added descriptions for each component
- Included the new YAML anchor approach in docker-compose.yml

### 3. **Enhanced Configuration Section**
- Detailed environment variables explanation
- Docker Compose service inheritance description
- Configuration examples and best practices

### 4. **Expanded API Documentation**
- Complete endpoint listing with examples
- Swagger UI and ReDoc integration details
- Authentication and security information

### 5. **Improved Troubleshooting**
- Common issues and solutions
- Performance tuning recommendations
- Log access and debugging commands

### 6. **Advanced Usage Examples**
- Scaling services
- Custom configuration
- Backup and recovery procedures

### 7. **Professional Documentation**
- Clear structure with emojis for visual appeal
- Comprehensive sections covering all aspects
- Contributing guidelines and license information

This README now accurately reflects the latest state of your SeaweedFS HA Demo project, including all the recent improvements to the docker-compose.yml, nginx configuration, API enhancements, and dashboard updates! 🎯

**Note:** Make sure to update the repository URL and any specific configuration details that are unique to your setup. The README assumes standard configurations - adjust as needed for your environment.