#!/usr/bin/env python3

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import docker
import json
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import urllib.parse
import secrets
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import requests

# Pydantic models for better Swagger documentation
class ContainerStatus(BaseModel):
    name: str = Field(..., description="Container name")
    status: str = Field(..., description="Current container status (running, exited, etc.)")
    container_id: str = Field(..., description="Short container ID")
    image: str = Field(..., description="Docker image name and tag")

class ContainerHealth(BaseModel):
    container: str = Field(..., description="Container name")
    status: str = Field(..., description="Health status (healthy, unhealthy, unknown)")
    overall_status: str = Field(..., description="Overall container status")

class S3Operation(BaseModel):
    timestamp: str = Field(..., description="Operation timestamp in ISO format")
    operation: str = Field(..., description="S3 operation type (GET, PUT, etc.)")
    bucket: str = Field(..., description="S3 bucket name")
    key: str = Field(..., description="S3 object key")
    size: int = Field(..., description="Object size in bytes")

class S3ObjectInfo(BaseModel):
    bucket: str = Field(..., description="S3 bucket name")
    key: str = Field(..., description="S3 object key")
    size: int = Field(..., description="Object size in bytes")
    last_modified: str = Field(..., description="Last modified timestamp")
    etag: str = Field(..., description="Object ETag")

class S3BucketInfo(BaseModel):
    name: str = Field(..., description="Bucket name")
    creation_date: Optional[str] = Field(None, description="Bucket creation date")

class HealthResponse(BaseModel):
    status: str = Field(..., description="API health status")
    timestamp: str = Field(..., description="Current timestamp")
    service: str = Field(..., description="Service name")

class ContainerList(BaseModel):
    containers: List[ContainerStatus] = Field(..., description="List of containers")

class S3OperationsResponse(BaseModel):
    operations: List[S3Operation] = Field(..., description="List of S3 operations")

class S3ObjectsResponse(BaseModel):
    objects: List[S3ObjectInfo] = Field(..., description="List of S3 objects")

class S3BucketsResponse(BaseModel):
    buckets: List[S3BucketInfo] = Field(..., description="List of S3 buckets")

app = FastAPI(
    title="SeaweedFS Cluster Management API",
    description="""
    # SeaweedFS Cluster Management API

    This comprehensive API provides full management capabilities for your SeaweedFS distributed file system cluster.

    ## 🚀 Features

    * **Container Management**: Start, stop, and monitor SeaweedFS containers
    * **Health Monitoring**: Real-time health checks for all cluster components
    * **S3 Operations**: Full S3-compatible operations for buckets and objects
    * **Interactive Documentation**: Full Swagger UI and ReDoc for testing endpoints

    ## 🔐 Authentication

    All endpoints are protected by HTTP Basic Authentication through the nginx proxy.
    Use the credentials configured in your setup (default: admin/seaweedadmin).

    ## 📚 Getting Started

    1. Access the interactive documentation at `/docs`
    2. Use the "Authorize" button to enter your credentials (if required)
    3. Test any endpoint directly from the Swagger UI
    4. All requests will be authenticated through the nginx proxy

    ## 📋 API Endpoints Overview

    ### Container Management
    - `GET /api/health` - Service health check
    - `GET /api/containers/{container_name}` - Get container status
    - `GET /api/containers/{container_name}/health` - Get container health
    - `POST /api/containers/{container_name}` - Start container
    - `DELETE /api/containers/{container_name}` - Stop container
    - `GET /api/containers` - List all containers

    ### S3 Operations
    - `GET /api/s3/buckets` - List all buckets
    - `PUT /api/s3/buckets/{bucket_name}` - Create bucket
    - `DELETE /api/s3/buckets/{bucket_name}` - Delete bucket
    - `GET /api/s3/buckets/{bucket_name}/objects` - List objects in bucket
    - `POST /api/s3/buckets/{bucket_name}/objects/{object_key}` - Create/update object
    - `GET /api/s3/buckets/{bucket_name}/objects/{object_key}` - Get object
    - `DELETE /api/s3/buckets/{bucket_name}/objects/{object_key}` - Delete object
    - `GET /api/s3-operations` - Get S3 operations (mock data)

    ## 🏷️ Tags

    - **Health**: Health check and monitoring endpoints
    - **Containers**: Container management operations
    - **S3**: S3-compatible operations for buckets and objects

    ## 📞 Support

    For issues or questions, please check the SeaweedFS documentation or contact your system administrator.
    """,
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    contact={
        "name": "SeaweedFS Cluster Admin",
        "url": "https://github.com/chrislusf/seaweedfs",
        "email": "admin@seaweedfs.local",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
    swagger_ui_parameters={
        "persistAuthorization": True,
        "displayRequestDuration": True,
        "docExpansion": "none",
        "filter": True,
        "showExtensions": True,
        "showCommonExtensions": True,
        "tryItOutEnabled": True,
        "syntaxHighlight.theme": "arta",
        "defaultModelsExpandDepth": 1,
        "defaultModelExpandDepth": 1,
        "displayOperationId": False,
        "displayRequestDuration": True,
        "deepLinking": True,
        "showMutatedRequest": True,
    },
    tags_metadata=[
        {
            "name": "Health",
            "description": "Health check and monitoring endpoints",
        },
        {
            "name": "Containers",
            "description": "Container management operations",
        },
        {
            "name": "S3",
            "description": "S3-compatible operations for buckets and objects",
        },
    ]
)

# CORS middleware - allow all for Swagger UI functionality
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security scheme for Swagger UI
security = HTTPBasic()

# S3 client dependency
def get_s3_client():
    """Create and return S3 client for SeaWeedFS"""
    try:
        s3_url = os.getenv('SEAWEED_S3_URL', 'http://s3_1:8333')
        access_key = os.getenv('AWS_ACCESS_KEY_ID')
        secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        
        if not access_key or not secret_key:
            raise HTTPException(status_code=500, detail="S3 credentials not configured. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in environment variables.")
        
        return boto3.client(
            's3',
            endpoint_url=s3_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=os.getenv('AWS_DEFAULT_REGION', ''),
            config=boto3.session.Config(
                signature_version='s3v4',
                s3={'addressing_style': os.getenv('AWS_S3_ADDRESSING_STYLE', 'path')}
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"S3 client initialization failed: {str(e)}")

# Docker client dependency
def get_docker_client():
    try:
        return docker.from_env()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Docker connection failed: {str(e)}")

@app.get("/api/health", 
         summary="Health Check", 
         description="Returns the current health status of the API service",
         response_model=HealthResponse,
         tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "SeaweedFS Cluster API"
    }

@app.get("/api/containers/{container_name}", 
         summary="Get Container Status",
         description="Retrieve the current status and information of a specific container",
         response_model=ContainerStatus,
         tags=["Containers"],
         responses={
             200: {
                 "description": "Container status retrieved successfully",
                 "content": {
                     "application/json": {
                         "example": {
                             "name": "master1",
                             "status": "running",
                             "container_id": "abc12345",
                             "image": "seaweedfs/master:latest"
                         }
                     }
                 }
             },
             404: {
                 "description": "Container not found",
                 "content": {
                     "application/json": {
                         "example": {"detail": "Container 'master1' not found"}
                     }
                 }
             }
         })
async def get_container_status(container_name: str, client: docker.DockerClient = Depends(get_docker_client)):
    """
    Get detailed status information for a container.
    
    - **container_name**: The name of the container to query (e.g., master1, volume1, filer1)
    - Returns container status, ID, and image information
    """
    try:
        if not container_name or container_name.strip() == "":
            raise HTTPException(status_code=400, detail="Container name cannot be empty")

        container = client.containers.get(container_name)
        return {
            "name": container.name,
            "status": container.status,
            "container_id": container.id[:12],
            "image": container.image.tags[0] if container.image.tags else "unknown"
        }
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail=f"Container '{container_name}' not found")
    except docker.errors.APIError as e:
        raise HTTPException(status_code=500, detail=f"Docker API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.get("/api/containers/{container_name}/health",
         summary="Get Container Health",
         description="Check the health status of a specific container using service-specific health checks",
         response_model=ContainerHealth,
         tags=["Containers"],
         responses={
             200: {
                 "description": "Container health retrieved successfully",
                 "content": {
                     "application/json": {
                         "example": {
                             "container": "master1",
                             "status": "healthy",
                             "overall_status": "running"
                         }
                     }
                 }
             },
             404: {
                 "description": "Container not found",
                 "content": {
                     "application/json": {
                         "example": {"detail": "Container 'master1' not found"}
                     }
                 }
             }
         })
async def get_container_health(container_name: str, client: docker.DockerClient = Depends(get_docker_client)):
    """
    Get health status for a container.
    
    Performs health checks based on container type:
    - **Filers**: Check HTTP endpoint on port 8888
    - **Masters**: Check cluster status on port 9333  
    - **Volumes**: Check status endpoint on port 8080
    - **S3 Gateways**: Check S3 endpoint on port 8333
    
    - **container_name**: The name of the container to check
    - Returns health status and overall container status
    """
    try:
        if not container_name:
            raise HTTPException(status_code=400, detail="Container name cannot be empty")
        
        container = client.containers.get(container_name)
        health_status = "unknown"
        
        # Check health based on container type
        container_type = get_container_type(container.name)

        if container_type == 'filer':
            # For filers, check HTTP endpoint
            try:
                import requests
                response = requests.get(f"http://{container_name}:8888/", timeout=5)
                health_status = "healthy" if response.status_code == 200 else "unhealthy"
            except:
                health_status = "unhealthy"
        elif container_type == 'master':
            # For masters, check cluster status
            try:
                import requests
                response = requests.get(f"http://{container_name}:9333/cluster/status", timeout=5)
                health_status = "healthy" if response.status_code == 200 else "unhealthy"
            except:
                health_status = "unhealthy"
        elif container_type == 'volume':
            # For volumes, check status endpoint
            try:
                import requests
                response = requests.get(f"http://{container_name}:8080/status", timeout=5)
                health_status = "healthy" if response.status_code == 200 else "unhealthy"
            except:
                health_status = "unhealthy"
        elif container_type == 's3':
            # For S3 gateways, check S3 endpoint (accepts 200 or 403 as healthy)
            try:
                import requests
                response = requests.get(f"http://{container_name}:8333", timeout=5)
                health_status = "healthy" if response.status_code in [200, 403] else "unhealthy"
            except:
                health_status = "unhealthy"
        
        return {
            "container": container_name,
            "status": health_status,
            "overall_status": container.status
        }
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail=f"Container '{container_name}' not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/containers/{container_name}",
          summary="Start Container", 
          description="Start a stopped container in the cluster",
          tags=["Containers"],
          responses={
              200: {
                  "description": "Container started successfully",
                  "content": {
                      "application/json": {
                          "example": {"message": "Container master1 started successfully"}
                      }
                  }
              },
              404: {
                  "description": "Container not found",
                  "content": {
                      "application/json": {
                          "example": {"detail": "Container 'master1' not found"}
                      }
                  }
              }
          })
async def start_container(container_name: str, client: docker.DockerClient = Depends(get_docker_client)):
    """
    Start a container that is currently stopped.
    
    - **container_name**: The name of the container to start
    - Returns success message if container starts successfully
    """
    try:
        if not container_name:
            raise HTTPException(status_code=400, detail="Container name cannot be empty")
        
        container = client.containers.get(container_name)
        
        # Check if container is already running
        if container.status == "running":
            return {"message": f"Container {container_name} is already running"}
        
        container.start()
        return {"message": f"Container {container_name} started successfully"}
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail=f"Container '{container_name}' not found")
    except docker.errors.APIError as e:
        # Handle specific Docker API errors
        if "already in progress" in str(e).lower():
            return {"message": f"Container {container_name} start already in progress"}
        elif "not running" in str(e).lower():
            return {"message": f"Container {container_name} is not running"}
        else:
            raise HTTPException(status_code=500, detail=f"Docker API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.delete("/api/containers/{container_name}",
            summary="Stop Container",
            description="Stop a running container in the cluster", 
            tags=["Containers"],
            responses={
                200: {
                    "description": "Container stopped successfully",
                    "content": {
                        "application/json": {
                            "example": {"message": "Container master1 stopped successfully"}
                        }
                    }
                },
                404: {
                    "description": "Container not found",
                    "content": {
                        "application/json": {
                            "example": {"detail": "Container 'master1' not found"}
                        }
                    }
                }
            })
async def stop_container(container_name: str, client: docker.DockerClient = Depends(get_docker_client)):
    """
    Stop a container that is currently running.
    
    - **container_name**: The name of the container to stop
    - Returns success message if container stops successfully
    """
    try:
        if not container_name:
            raise HTTPException(status_code=400, detail="Container name cannot be empty")

        container = client.containers.get(container_name)
        
        # Check if container is already stopped
        if container.status == "exited":
            return {"message": f"Container {container_name} is already stopped"}
        
        container.stop(timeout=30)  # Add timeout to prevent hanging
        return {"message": f"Container {container_name} stopped successfully"}
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail=f"Container '{container_name}' not found")
    except docker.errors.APIError as e:
        # Handle specific Docker API errors
        if "not running" in str(e).lower():
            return {"message": f"Container {container_name} is not running"}
        elif "already in progress" in str(e).lower():
            return {"message": f"Container {container_name} stop already in progress"}
        else:
            raise HTTPException(status_code=500, detail=f"Docker API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.get("/api/s3-operations",
         summary="Get S3 Operations",
         description="Retrieve mock S3 operation data for monitoring and testing",
         response_model=S3OperationsResponse,
         tags=["S3"],
         responses={
             200: {
                 "description": "S3 operations retrieved successfully",
                 "content": {
                     "application/json": {
                         "example": {
                             "operations": [
                                 {
                                     "timestamp": "2025-09-09T14:28:30.123456Z",
                                     "operation": "PUT",
                                     "bucket": "test-bucket",
                                     "key": "test-file.txt",
                                     "size": 1024
                                 }
                             ]
                         }
                     }
                 }
             }
         })
async def get_s3_operations(since: Optional[str] = None):
    """
    Get mock S3 operations data.
    
    Returns a list of simulated S3 operations for testing and monitoring purposes.
    
    - **since**: Optional timestamp filter (not implemented in mock)
    - Returns list of operation records with timestamps, operations, and metadata
    """
    try:
        # Mock S3 operations data
        operations = [
            {
                "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                "operation": "PUT",
                "bucket": "test-bucket",
                "key": "test-file.txt",
                "size": 1024
            },
            {
                "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                "operation": "GET",
                "bucket": "test-bucket", 
                "key": "test-file.txt",
                "size": 1024
            }
        ]
        
        return {"operations": operations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/containers",
         summary="List All Containers",
         description="List all containers in the cluster with their status information",
         response_model=ContainerList,
         tags=["Containers"],
         responses={
             200: {
                 "description": "Containers listed successfully",
                 "content": {
                     "application/json": {
                         "example": {
                             "containers": [
                                 {
                                     "name": "master1",
                                     "status": "running",
                                     "container_id": "abc12345",
                                     "image": "seaweedfs/master:latest"
                                 }
                             ]
                         }
                     }
                 }
             }
         })
async def list_containers(client: docker.DockerClient = Depends(get_docker_client)):
    """
    List all containers in the SeaweedFS cluster.
    
    Returns information about all master, volume, and filer containers including:
    - Container name
    - Current status
    - Docker image
    
    Only shows containers related to SeaweedFS (containing 'master', 'volume', or 'filer' in name).
    """
    try:
        containers = client.containers.list(all=True)
        return {
            "containers": [
                {
                    "name": container.name,
                    "status": container.status,
                    "container_id": container.id[:12],  # Fixed: Added missing container_id field
                    "image": container.image.tags[0] if container.image.tags else "unknown"
                }
                for container in containers
                if any(keyword in container.name.lower() for keyword in ['master', 'volume', 'filer', 's3'])
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# S3 Bucket Operations
@app.get("/api/s3/buckets",
         summary="List S3 Buckets",
         description="List all S3 buckets in the SeaweedFS cluster",
         response_model=S3BucketsResponse,
         tags=["S3"],
         responses={
             200: {
                 "description": "Buckets listed successfully",
                 "content": {
                     "application/json": {
                         "example": {
                             "buckets": [
                                 {
                                     "name": "test-bucket",
                                     "creation_date": "2025-09-09T14:28:30.123456Z"
                                 }
                             ]
                         }
                     }
                 }
             }
         })
async def list_s3_buckets(s3_client = Depends(get_s3_client)):
    """
    List all S3 buckets.
    
    Returns a list of all buckets in the SeaweedFS S3 service.
    """
    try:
        response = s3_client.list_buckets()
        buckets = [
            {
                "name": bucket['Name'],
                "creation_date": bucket['CreationDate'].isoformat() if bucket.get('CreationDate') else None
            }
            for bucket in response.get('Buckets', [])
        ]
        return {"buckets": buckets}
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code in ['EndpointConnectionError', 'NetworkError', 'ConnectionError']:
            raise HTTPException(status_code=503, detail="S3 service is not available. Please check if the S3 container is running and accessible.")
        else:
            raise HTTPException(status_code=500, detail=f"S3 error: {error_code} - {e.response['Error']['Message']}")
    except Exception as e:
        if 'connection' in str(e).lower() or 'endpoint' in str(e).lower():
            raise HTTPException(status_code=503, detail="S3 service is not available. Please check if the S3 container is running and accessible.")
        else:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.put("/api/s3/buckets/{bucket_name}",
         summary="Create S3 Bucket",
         description="Create a new S3 bucket in the SeaweedFS cluster",
         tags=["S3"],
         responses={
             200: {
                 "description": "Bucket created successfully",
                 "content": {
                     "application/json": {
                         "example": {"message": "Bucket 'test-bucket' created successfully"}
                     }
                 }
             },
             409: {
                 "description": "Bucket already exists",
                 "content": {
                     "application/json": {
                         "example": {"detail": "Bucket 'test-bucket' already exists"}
                     }
                 }
             }
         })
async def create_s3_bucket(bucket_name: str, s3_client = Depends(get_s3_client)):
    """
    Create a new S3 bucket.
    
    - **bucket_name**: Name of the bucket to create
    - Returns success message if bucket is created
    """
    try:
        s3_client.create_bucket(Bucket=bucket_name)
        return {"message": f"Bucket '{bucket_name}' created successfully"}
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code in ['BucketAlreadyExists', 'BucketAlreadyOwnedByYou']:
            raise HTTPException(status_code=409, detail=f"Bucket '{bucket_name}' already exists")
        elif error_code in ['EndpointConnectionError', 'NetworkError', 'ConnectionError']:
            raise HTTPException(status_code=503, detail="S3 service is not available. Please check if the S3 container is running and accessible.")
        else:
            raise HTTPException(status_code=500, detail=f"S3 error: {error_code} - {e.response['Error']['Message']}")
    except Exception as e:
        if 'connection' in str(e).lower() or 'endpoint' in str(e).lower():
            raise HTTPException(status_code=503, detail="S3 service is not available. Please check if the S3 container is running and accessible.")
        else:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.delete("/api/s3/buckets/{bucket_name}",
            summary="Delete S3 Bucket",
            description="Delete an empty S3 bucket from the SeaweedFS cluster",
            tags=["S3"],
            responses={
                200: {
                    "description": "Bucket deleted successfully",
                    "content": {
                        "application/json": {
                            "example": {"message": "Bucket 'test-bucket' deleted successfully"}
                        }
                    }
                },
                404: {
                    "description": "Bucket not found",
                    "content": {
                        "application/json": {
                            "example": {"detail": "Bucket 'test-bucket' not found"}
                        }
                    }
                }
            })
async def delete_s3_bucket(bucket_name: str, s3_client = Depends(get_s3_client)):
    """
    Delete an S3 bucket.
    
    The bucket must be empty before deletion.
    
    - **bucket_name**: Name of the bucket to delete
    - Returns success message if bucket is deleted
    """
    try:
        s3_client.delete_bucket(Bucket=bucket_name)
        return {"message": f"Bucket '{bucket_name}' deleted successfully"}
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchBucket':
            raise HTTPException(status_code=404, detail=f"Bucket '{bucket_name}' not found")
        elif error_code == 'BucketNotEmpty':
            raise HTTPException(status_code=409, detail=f"Bucket '{bucket_name}' is not empty")
        elif error_code in ['EndpointConnectionError', 'NetworkError', 'ConnectionError']:
            raise HTTPException(status_code=503, detail="S3 service is not available. Please check if the S3 container is running and accessible.")
        else:
            raise HTTPException(status_code=500, detail=f"S3 error: {error_code} - {e.response['Error']['Message']}")
    except Exception as e:
        if 'connection' in str(e).lower() or 'endpoint' in str(e).lower():
            raise HTTPException(status_code=503, detail="S3 service is not available. Please check if the S3 container is running and accessible.")
        else:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# S3 Object Operations
@app.get("/api/s3/buckets/{bucket_name}/objects",
         summary="List S3 Objects",
         description="List all objects in an S3 bucket",
         response_model=S3ObjectsResponse,
         tags=["S3"],
         responses={
             200: {
                 "description": "Objects listed successfully",
                 "content": {
                     "application/json": {
                         "example": {
                             "objects": [
                                 {
                                     "bucket": "test-bucket",
                                     "key": "test-file.txt",
                                     "size": 1024,
                                     "last_modified": "2025-09-09T14:28:30.123456Z",
                                     "etag": "\"abc123\""
                                 }
                             ]
                         }
                     }
                 }
             },
             404: {
                 "description": "Bucket not found",
                 "content": {
                     "application/json": {
                         "example": {"detail": "Bucket 'test-bucket' not found"}
                     }
                 }
             }
         })
async def list_s3_objects(bucket_name: str, s3_client = Depends(get_s3_client)):
    """
    List all objects in an S3 bucket.
    
    - **bucket_name**: Name of the bucket to list objects from
    - Returns list of objects with metadata
    """
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        objects = [
            {
                "bucket": bucket_name,
                "key": obj['Key'],
                "size": obj.get('Size', 0),
                "last_modified": obj['LastModified'].isoformat() if obj.get('LastModified') else None,
                "etag": obj.get('ETag', '')
            }
            for obj in response.get('Contents', [])
        ]
        return {"objects": objects}
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchBucket':
            raise HTTPException(status_code=404, detail=f"Bucket '{bucket_name}' not found")
        elif error_code in ['EndpointConnectionError', 'NetworkError', 'ConnectionError']:
            raise HTTPException(status_code=503, detail="S3 service is not available. Please check if the S3 container is running and accessible.")
        else:
            raise HTTPException(status_code=500, detail=f"S3 error: {error_code} - {e.response['Error']['Message']}")
    except Exception as e:
        if 'connection' in str(e).lower() or 'endpoint' in str(e).lower():
            raise HTTPException(status_code=503, detail="S3 service is not available. Please check if the S3 container is running and accessible.")
        else:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.post("/api/s3/buckets/{bucket_name}/objects/{object_key}",
          summary="Create/Update S3 Object",
          description="Create or update an S3 object with provided content",
          tags=["S3"],
          responses={
              200: {
                  "description": "Object created/updated successfully",
                  "content": {
                      "application/json": {
                          "example": {
                              "message": "Object 'test-file.txt' created successfully",
                              "bucket": "test-bucket",
                              "key": "test-file.txt",
                              "size": 1024
                          }
                      }
                  }
              },
              404: {
                  "description": "Bucket not found",
                  "content": {
                      "application/json": {
                          "example": {"detail": "Bucket 'test-bucket' not found"}
                      }
                  }
              }
          })
async def create_s3_object(bucket_name: str, object_key: str, content: str = "", size_kb: int = 10, s3_client = Depends(get_s3_client)):
    """
    Create or update an S3 object.
    
    - **bucket_name**: Name of the bucket
    - **object_key**: Key of the object to create/update
    - **content**: Content to store in the object (optional)
    - **size_kb**: Size of the object in KB (for mock content generation)
    - Returns success message with object details
    """
    try:
        # Generate mock content if not provided
        if not content:
            content = "x" * (size_kb * 1024)  # Generate content of specified size
        
        s3_client.put_object(
            Bucket=bucket_name,
            Key=object_key,
            Body=content.encode('utf-8')
        )
        
        return {
            "message": f"Object '{object_key}' created successfully",
            "bucket": bucket_name,
            "key": object_key,
            "size": len(content)
        }
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchBucket':
            # Auto-create bucket if it doesn't exist
            try:
                s3_client.create_bucket(Bucket=bucket_name)
                # Retry put_object
                s3_client.put_object(
                    Bucket=bucket_name,
                    Key=object_key,
                    Body=content.encode('utf-8')
                )
                return {
                    "message": f"Bucket '{bucket_name}' created and object '{object_key}' uploaded successfully",
                    "bucket": bucket_name,
                    "key": object_key,
                    "size": len(content)
                }
            except ClientError as create_e:
                if create_e.response['Error']['Code'] in ['BucketAlreadyExists', 'BucketAlreadyOwnedByYou']:
                    raise HTTPException(status_code=500, detail=f"Bucket '{bucket_name}' exists but object upload failed: {create_e.response['Error']['Message']}")
                else:
                    raise HTTPException(status_code=500, detail=f"Failed to create bucket '{bucket_name}': {create_e.response['Error']['Message']}")
        elif error_code in ['EndpointConnectionError', 'NetworkError', 'ConnectionError']:
            raise HTTPException(status_code=503, detail="S3 service is not available. Please check if the S3 container is running and accessible.")
        else:
            raise HTTPException(status_code=500, detail=f"S3 error: {error_code} - {e.response['Error']['Message']}")
    except Exception as e:
        if 'connection' in str(e).lower() or 'endpoint' in str(e).lower():
            raise HTTPException(status_code=503, detail="S3 service is not available. Please check if the S3 container is running and accessible.")
        else:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.get("/api/s3/buckets/{bucket_name}/objects/{object_key}",
         summary="Get S3 Object",
         description="Retrieve an S3 object's content and metadata",
         tags=["S3"],
         responses={
             200: {
                 "description": "Object retrieved successfully",
                 "content": {
                     "application/json": {
                         "example": {
                             "bucket": "test-bucket",
                             "key": "test-file.txt",
                             "size": 1024,
                             "content": "file content here...",
                             "last_modified": "2025-09-09T14:28:30.123456Z",
                             "etag": "\"abc123\""
                         }
                     }
                 }
             },
             404: {
                 "description": "Object not found",
                 "content": {
                     "application/json": {
                         "example": {"detail": "Object 'test-file.txt' not found in bucket 'test-bucket'"}
                     }
                 }
             }
         })
async def get_s3_object(bucket_name: str, object_key: str, s3_client = Depends(get_s3_client)):
    """
    Get an S3 object's content and metadata.
    
    - **bucket_name**: Name of the bucket
    - **object_key**: Key of the object to retrieve
    - Returns object content and metadata
    """
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        
        content = response['Body'].read().decode('utf-8')
        
        return {
            "bucket": bucket_name,
            "key": object_key,
            "size": response.get('ContentLength', 0),
            "content": content,
            "last_modified": response['LastModified'].isoformat() if response.get('LastModified') else None,
            "etag": response.get('ETag', '')
        }
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchBucket':
            raise HTTPException(status_code=404, detail=f"Bucket '{bucket_name}' not found")
        elif error_code == 'NoSuchKey':
            raise HTTPException(status_code=404, detail=f"Object '{object_key}' not found in bucket '{bucket_name}'")
        elif error_code in ['EndpointConnectionError', 'NetworkError', 'ConnectionError']:
            raise HTTPException(status_code=503, detail="S3 service is not available. Please check if the S3 container is running and accessible.")
        else:
            raise HTTPException(status_code=500, detail=f"S3 error: {error_code} - {e.response['Error']['Message']}")
    except Exception as e:
        if 'connection' in str(e).lower() or 'endpoint' in str(e).lower():
            raise HTTPException(status_code=503, detail="S3 service is not available. Please check if the S3 container is running and accessible.")
        else:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.delete("/api/s3/buckets/{bucket_name}/objects/{object_key}",
            summary="Delete S3 Object",
            description="Delete an S3 object from a bucket",
            tags=["S3"],
            responses={
                200: {
                    "description": "Object deleted successfully",
                    "content": {
                        "application/json": {
                            "example": {
                                "message": "Object 'test-file.txt' deleted successfully",
                                "bucket": "test-bucket",
                                "key": "test-file.txt"
                            }
                        }
                    }
                },
                404: {
                    "description": "Object not found",
                    "content": {
                        "application/json": {
                            "example": {"detail": "Object 'test-file.txt' not found in bucket 'test-bucket'"}
                        }
                    }
                }
            })
async def delete_s3_object(bucket_name: str, object_key: str, s3_client = Depends(get_s3_client)):
    """
    Delete an S3 object.
    
    - **bucket_name**: Name of the bucket
    - **object_key**: Key of the object to delete
    - Returns success message if object is deleted
    """
    try:
        s3_client.delete_object(Bucket=bucket_name, Key=object_key)
        
        return {
            "message": f"Object '{object_key}' deleted successfully",
            "bucket": bucket_name,
            "key": object_key
        }
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchBucket':
            raise HTTPException(status_code=404, detail=f"Bucket '{bucket_name}' not found")
        elif error_code == 'NoSuchKey':
            raise HTTPException(status_code=404, detail=f"Object '{object_key}' not found in bucket '{bucket_name}'")
        elif error_code in ['EndpointConnectionError', 'NetworkError', 'ConnectionError']:
            raise HTTPException(status_code=503, detail="S3 service is not available. Please check if the S3 container is running and accessible.")
        else:
            raise HTTPException(status_code=500, detail=f"S3 error: {error_code} - {e.response['Error']['Message']}")
    except Exception as e:
        if 'connection' in str(e).lower() or 'endpoint' in str(e).lower():
            raise HTTPException(status_code=503, detail="S3 service is not available. Please check if the S3 container is running and accessible.")
        else:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

def get_container_type(container_name: str) -> str:
    """Determine container type from name"""
    if 'filer' in container_name.lower():
        return 'filer'
    elif 'master' in container_name.lower():
        return 'master'
    elif 'volume' in container_name.lower():
        return 'volume'
    elif 's3' in container_name.lower():
        return 's3'
    return 'unknown'

def get_health_check_url(container_name: str) -> str:
    """Generate health check URL based on container type"""
    container_type = get_container_type(container_name)
    
    if container_type == 'filer':
        return f"http://{container_name}:8888/"
    elif container_type == 'master':
        return f"http://{container_name}:9333/cluster/status"
    elif container_type == 'volume':
        return f"http://{container_name}:8080/status"
    elif container_type == 's3':
        return f"http://{container_name}:8333"
    else:
        return None

# Custom OpenAPI schema with enhanced metadata
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        contact=app.contact,
        license_info=app.license_info,
    )
    # Add custom server information
    openapi_schema["servers"] = [
        {
            "url": "http://192.168.80.115",
            "description": "Production server"
        }
    ]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)