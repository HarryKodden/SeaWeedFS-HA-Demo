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

class HealthResponse(BaseModel):
    status: str = Field(..., description="API health status")
    timestamp: str = Field(..., description="Current timestamp")
    service: str = Field(..., description="Service name")

class ContainerList(BaseModel):
    containers: List[ContainerStatus] = Field(..., description="List of containers")

class S3OperationsResponse(BaseModel):
    operations: List[S3Operation] = Field(..., description="List of S3 operations")

app = FastAPI(
    title="SeaweedFS Cluster Management API",
    description="""
    # SeaweedFS Cluster Management API

    This comprehensive API provides full management capabilities for your SeaweedFS distributed file system cluster.

    ## 🚀 Features

    * **Container Management**: Start, stop, and monitor SeaweedFS containers
    * **Health Monitoring**: Real-time health checks for all cluster components
    * **S3 Operations**: Mock S3 operation data for testing and monitoring
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
    - `GET /api/s3-operations` - Get S3 operations (mock data)

    ## 🏷️ Tags

    - **Health**: Health check and monitoring endpoints
    - **Containers**: Container management operations
    - **S3**: S3-related operations and data

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
            "description": "S3-related operations and data",
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
                if any(keyword in container.name.lower() for keyword in ['master', 'volume', 'filer'])
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_container_type(container_name: str) -> str:
    """Determine container type from name"""
    if 'filer' in container_name.lower():
        return 'filer'
    elif 'master' in container_name.lower():
        return 'master'
    elif 'volume' in container_name.lower():
        return 'volume'
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