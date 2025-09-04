# SeaweedFS Docker Compose Architecture

## Overview
SeaweedFS is a distributed file system with features like S3 compatibility, high availability, and scalability. Your setup uses Docker Compose to orchestrate multiple containers that work together to provide storage services.

## Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                        │
│                            Client (Browser/API Client)                                                 │
│                                                                                                        │
└────────────────────────────────────────┬───────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                        │
│                                   Public Internet                                                      │
│                                                                                                        │
└───────────┬────────────────────────────┬───────────────────────────────────┬───────────────────────────┘
            │                            │                                   │
            │                            │                                   │
            ▼                            ▼                                   ▼
┌─────────────────────────┐  ┌─────────────────────────┐  ┌──────────────────────────────────────────────┐
│ seaweed-master.${DOMAIN}│  │ seaweed-volume.${DOMAIN}│  │    seaweed.${DOMAIN}    seaweed-s3.${DOMAIN} │
└───────────┬─────────────┘  └───────────┬─────────────┘  └──────────────────┬───────────────────────────┘
            │                            │                                   │
            │                            │                                   │
            ▼                            ▼                                   ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                        │
│                             Traefik Reverse Proxy                                                      │
│                               (TLS termination)                                                        │
│                                                                                                        │
└───────────┬────────────────────────────┬───────────────────────────────────┬───────────────────────────┘
            │                            │                                   │
            │                            │                                   │
            ▼                            ▼                                   ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                        │
│                                External Network                                                        │
│                                                                                                        │
└────────────────────────────────────────┬───────────────────────────────────────────────────────────────┘
                                         │
                                         │
                                         ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                        │
│                                                   Internal Network                                     │
│                                                                                                        │
└───────────┬────────────────────────────┬───────────────────────────────────┬───────────────────────────┘
            │                            │                                   │
            │                            │                                   │
            ▼                            ▼                                   ▼
┌─────────────────────┐      ┌───────────────────────┐       ┌───────────────────────────────────────────┐
│                     │      │                       │       │                                           │
│    Master Server    │      │    Volume Server      │       │  Filer Server                             │
│    (master:9333)    │◄---─►│    (volume:8080)      │◄─----►│  (filer:8888, S3:8333)                    │
│                     │      │                       │       │                                           │
└───────────┬─────────┘      └───────────┬───────────┘       └───────────────┬───────────────────────────┘
            │                            │                                   │
            │                            │                                   │
            ▼                            ▼                                   ▼
┌─────────────────────┐      ┌───────────────────────┐       ┌───────────────────────────────────────────┐
│    No Persistent    │      │     volume:/data      │       │           filer:/data                     │
│       Storage       │      │     (Volumes Data)    │       │        (Metadata Storage)                 │
└─────────────────────┘      └───────────────────────┘       └───────────────────────────────────────────┘
```

## Components

### 1. Master Server
- **Container Name**: demo-master-1
- **Service Name**: master
- **Main Port**: 9333
- **Role**: Coordinates the cluster and manages volume servers
- **Functions**:
  - Maintains the topology of the cluster
  - Assigns volume IDs
  - Manages volume placement and replicas
  - Provides cluster status information

### 2. Volume Server
- **Container Name**: demo-volume-1
- **Service Name**: volume
- **Main Port**: 8080
- **Role**: Stores the actual file data (chunks) on disk
- **Functions**:
  - Manages actual file data storage (arranged in volumes)
  - Handles read/write operations for file chunks
  - Communicates with master for coordination
  - Persistent storage using volume:/data Docker volume

### 3. Filer Server
- **Container Name**: demo-filer-1
- **Service Name**: filer
- **Main Ports**: 
  - 8888 (Filer API)
  - 8333 (S3 API)
- **Role**: Provides a unified namespace and S3-compatible API
- **Functions**:
  - Maps file paths to SeaweedFS volumes
  - Maintains directory structure and metadata
  - Provides S3-compatible API (port 8333)
  - Handles file operations (create, delete, list, etc.)
  - Persistent storage using filer:/data Docker volume
- **Environment Variables**:
  - AWS_ACCESS_KEY_ID
  - AWS_SECRET_ACCESS_KEY

## External Access via Traefik

Traefik serves as a reverse proxy in front of the SeaweedFS components, providing TLS termination and routing based on hostnames:

- **seaweed-master.${DOMAIN}** → Routes to Master Server (port 9333)
- **seaweed-volume.${DOMAIN}** → Routes to Volume Server (port 8080)
- **seaweed.${DOMAIN}** → Routes to Filer Server UI/API (port 8888)
- **seaweed-s3.${DOMAIN}** → Routes to Filer S3 API (port 8333)

All external connections are secured with TLS certificates obtained through Let's Encrypt (certresolver=le).

## Networks
- **External Network**: Connects to external services and Traefik
- **Internal Network**: Internal communication between SeaweedFS components

## Persistent Storage
- **volume**: Docker volume for storing actual file data
- **filer**: Docker volume for storing file metadata

## Health Checks
All services have health checks configured to ensure they are running correctly:
- Master: Checks http://master:9333/cluster/status
- Volume: Checks http://volume:8080/status
- Filer: Checks http://filer:8888/

## S3 API Usage
The Filer component provides S3 compatibility on port 8333, allowing you to:
- Create buckets
- Upload/download files
- List objects
- Use standard S3 client libraries like boto3

## Current Configuration
In your setup:
- All services are running
- S3 API is active with at least one bucket ("test-bucket")
- Services are networked both internally and externally
- Traefik is configured to:
  - Provide secure access via HTTPS (with automatic TLS certificates)
  - Route requests based on domain name to appropriate services
  - Enable external access without directly exposing container ports
  - Support custom domain names via the ${DOMAIN} environment variable
