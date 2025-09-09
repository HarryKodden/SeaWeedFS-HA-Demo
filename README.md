# SeaweedFS HA Cluster

This repository contains configuration files and scripts to set up a High Availability (HA) SeaweedFS cluster with a comprehensive management dashboard and REST API.

On this dashboard you can manipulate the cluster, turn nodes on/off and see how the cluster recovers from that. The S3 operations are continuously processed and monitored in real-time.

![Cluster](cluster.png)

## Architecture

The setup includes:
- **3 Master servers** in a Raft cluster for high availability
- **3 Volume servers** across different "racks" for data redundancy
- **2 Filer servers** for metadata management and redundancy
- **1 API server** providing REST API for cluster management
- **Nginx reverse proxy** for load balancing and unified access
- **S3-compatible API** for standard object storage access

## Port Assignments

- `80`: Cluster Management Dashboard and REST API (password protected)
- `8080`: Filer server web interface
- `8333`: S3 API endpoint

## Quick Start

1. **Clone and setup**:
   ```bash
   git clone https://github.com/HarryKodden/SeaWeedFS-HA-Demo.git
   cd SeaWeedFS-HA-Demo
   ./setup_cluster.sh [username] [password] [domain]
   ```

2. **Start the cluster**:
   ```bash
   docker compose up -d
   ```

3. **Test the setup**:
   ```bash
   ./test_cluster.sh
   ```

## Management Dashboard

### Web Interface
Access the cluster management dashboard at:
```
http://localhost:80/
```

**Features**:
- ✅ One-click access to all master and volume servers
- ✅ Real-time status monitoring of each component
- ✅ Container start/stop controls with visual feedback
- ✅ Live S3 operations stream with filtering
- ✅ Cluster health indicators and failover monitoring
- ✅ Interactive server management with animations

### REST API
The cluster provides a comprehensive REST API for programmatic access:

#### Interactive API Documentation
Explore and test all API endpoints interactively:
```
http://localhost:80/api/docs
```

This provides a **Swagger UI** interface where you can:
- View detailed API documentation
- Test endpoints directly in your browser
- See request/response schemas
- Execute real API calls with "Try it out" functionality

#### API Endpoints

**Health & Status**:
- `GET /health` - System health check
- `GET /api/containers/{name}` - Get container status
- `GET /api/containers/{name}/health` - Get detailed container health

**Container Management**:
- `POST /api/containers/{name}` - Start a container
- `DELETE /api/containers/{name}` - Stop a container

**S3 Operations**:
- `GET /s3-operations` - Get recent S3 operations
- `GET /s3-operations?since={timestamp}` - Get operations since timestamp

**Available Containers**:
- `master1`, `master2`, `master3` - SeaweedFS master nodes
- `volume1`, `volume2`, `volume3` - SeaweedFS volume servers
- `filer1`, `filer2` - SeaweedFS filer servers
- `nginx` - Load balancer and dashboard
- `api` - REST API server

#### API Examples

**Check container status**:
```bash
curl http://localhost:80/api/containers/master1
```

**Start a container**:
```bash
curl -X POST http://localhost:80/api/containers/volume1
```

**Stop a container**:
```bash
curl -X DELETE http://localhost:80/api/containers/volume1
```

**Get S3 operations**:
```bash
curl http://localhost:80/s3-operations
```

## S3 API Usage

The S3 API is accessible at `http://localhost:8333/` and can be used with standard S3 tools:

```bash
# Configure AWS CLI
AWS_ACCESS_KEY_ID="your_key_id" \
AWS_SECRET_ACCESS_KEY="your_secret_key" \
aws --endpoint-url http://localhost:8333 s3 ls

# Upload a file
aws --endpoint-url http://localhost:8333 s3 cp file.txt s3://mybucket/

# List buckets
aws --endpoint-url http://localhost:8333 s3 ls
```

## File Structure

```
SeaWeedFS-HA-Demo/
├── docker-compose.yml      # Container orchestration
├── proxy/
│   ├── nginx.conf         # Reverse proxy configuration
│   ├── cluster.html       # Management dashboard UI
│   └── Dockerfile         # Nginx container build
├── api/
│   ├── api.py            # REST API server implementation
│   └── requirements.txt   # Python dependencies
├── setup_cluster.sh       # Initial setup script
├── test_cluster.sh        # Cluster validation script
├── .env                   # Environment variables (created during setup)
├── .htpasswd             # HTTP authentication (created during setup)
└── README.md             # This file
```

## Development & Testing

### Running Tests
```bash
./test_cluster.sh
```

This validates:
- ✅ Container health status
- ✅ Filer web interface accessibility
- ✅ S3 API endpoint availability
- ✅ Dashboard authentication
- ✅ API server responsiveness

### API Development
The API server provides comprehensive endpoints for cluster management. Use the interactive Swagger documentation at `/api/docs` for development and testing.

### Container Logs
```bash
# View all logs
docker compose logs

# View specific service logs
docker compose logs api
docker compose logs nginx
docker compose logs master1
```

## Troubleshooting

### Common Issues

1. **Dashboard shows "Offline" status**:
   ```bash
   # Check API server
   curl http://localhost:8080/health
   # Restart API server
   docker compose restart api
   ```

2. **S3 operations not showing**:
   ```bash
   # Check filer connectivity
   curl http://localhost:8080/
   # Restart filers
   docker compose restart filer1 filer2
   ```

3. **Authentication issues**:
   ```bash
   # Check .htpasswd file
   cat .htpasswd
   # Recreate if missing
   ./setup_cluster.sh
   ```

4. **Container health checks failing**:
   ```bash
   # Check individual container status
   docker compose ps
   # View container logs
   docker compose logs <container_name>
   ```

### Manual Testing

```bash
# Test all endpoints
curl http://localhost:8080/                    # Filer UI
curl http://localhost:8333/                    # S3 API (should return 403)
curl -u admin:password http://localhost:80/    # Dashboard
curl http://localhost:80/api/docs             # API documentation
curl http://localhost:8080/health             # API health check
```

## Security Notes

- The dashboard requires HTTP Basic Authentication
- API endpoints are CORS-enabled for web access
- S3 API keys are generated during setup and stored in `.env`
- All services run in isolated Docker containers
- Nginx provides unified access with proper routing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with `./test_cluster.sh`
5. Submit a pull request

## License

This project is open source and available under the MIT License.
