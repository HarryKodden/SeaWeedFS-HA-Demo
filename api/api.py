#!/usr/bin/env python3

import http.server
import socketserver
import subprocess
import json
import urllib.parse
import urllib.request
import requests
from datetime import datetime, timezone
import base64
import time
import os
import boto3
from botocore.exceptions import ClientError

class ClusterAPIHandler(http.server.BaseHTTPRequestHandler):

    # healthcheck endpoint
    def handle_health_check(self):
        try:
            health_response = {
                "status": "healthy",
                "service": "SeaweedFS Cluster API",
                "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(health_response).encode())

        except Exception as e:
            self.send_error(500, f"Internal server error: {str(e)}")

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path_parts = parsed_path.path.strip('/').split('/')

        if parsed_path.path == '/health':
            self.handle_health_check()
        elif parsed_path.path == '/api/docs/openapi.json':
            self.serve_openapi_spec()
        elif parsed_path.path == '/api/docs':
            self.handle_api_docs()
        elif parsed_path.path == '/s3-operations':
            self.handle_s3_operations()
        elif len(path_parts) >= 4 and path_parts[0] == 'api' and path_parts[1] == 'containers' and path_parts[3] == 'health':
            container_name = path_parts[2]
            self.handle_container_health(container_name)
        elif len(path_parts) >= 3 and path_parts[0] == 'api' and path_parts[1] == 'containers':
            container_name = path_parts[2]
            self.handle_container_status(container_name)
        elif len(path_parts) >= 3 and path_parts[0] == 'containers' and path_parts[2] == 'health':
            container_name = path_parts[1]
            self.handle_container_health(container_name)
        elif len(path_parts) >= 2 and path_parts[0] == 'containers':
            container_name = path_parts[1]
            self.handle_container_status(container_name)
        elif len(path_parts) >= 5 and path_parts[0] == 'api' and path_parts[1] == 's3' and path_parts[2] == 'buckets':
            bucket_name = path_parts[3]
            object_key = '/'.join(path_parts[5:])  # Handle object keys with slashes
            self.handle_s3_object_read(bucket_name, object_key)
        else:
            self.send_error(404, "Endpoint not found")

        if parsed_path.path == '/health':
            self.handle_health_check()
        elif parsed_path.path == '/api/docs/openapi.json':
            self.serve_openapi_spec()
        elif parsed_path.path == '/api/docs':
            self.handle_api_docs()
        elif parsed_path.path == '/s3-operations':
            self.handle_s3_operations()
        elif len(path_parts) >= 4 and path_parts[0] == 'api' and path_parts[1] == 'containers' and path_parts[3] == 'health':
            container_name = path_parts[2]
            self.handle_container_health(container_name)
        elif len(path_parts) >= 3 and path_parts[0] == 'api' and path_parts[1] == 'containers':
            container_name = path_parts[2]
            self.handle_container_status(container_name)
        elif len(path_parts) >= 3 and path_parts[0] == 'containers' and path_parts[2] == 'health':
            container_name = path_parts[1]
            self.handle_container_health(container_name)
        elif len(path_parts) >= 2 and path_parts[0] == 'containers':
            container_name = path_parts[1]
            self.handle_container_status(container_name)
        elif len(path_parts) >= 5 and path_parts[0] == 'api' and path_parts[1] == 's3' and path_parts[2] == 'buckets':
            bucket_name = path_parts[3]
            object_key = '/'.join(path_parts[5:])  # Handle object keys with slashes
            self.handle_s3_object_read(bucket_name, object_key)
        else:
            self.send_error(404, "Endpoint not found")

    def do_POST(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path_parts = parsed_path.path.strip('/').split('/')

        if len(path_parts) >= 3 and path_parts[0] == 'api' and path_parts[1] == 'containers':
            container_name = path_parts[2]
            self.handle_container_start(container_name)
        elif len(path_parts) >= 2 and path_parts[0] == 'containers':
            container_name = path_parts[1]
            self.handle_container_start(container_name)
        elif len(path_parts) >= 5 and path_parts[0] == 'api' and path_parts[1] == 's3' and path_parts[2] == 'buckets':
            bucket_name = path_parts[3]
            object_key = '/'.join(path_parts[5:])  # Handle object keys with slashes
            self.handle_s3_object_create(bucket_name, object_key)
        else:
            self.send_error(404, "Endpoint not found")

    def do_DELETE(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path_parts = parsed_path.path.strip('/').split('/')

        if len(path_parts) >= 3 and path_parts[0] == 'api' and path_parts[1] == 'containers':
            container_name = path_parts[2]
            self.handle_container_stop(container_name)
        elif len(path_parts) >= 2 and path_parts[0] == 'containers':
            container_name = path_parts[1]
            self.handle_container_stop(container_name)
        elif len(path_parts) >= 5 and path_parts[0] == 'api' and path_parts[1] == 's3' and path_parts[2] == 'buckets':
            bucket_name = path_parts[3]
            object_key = '/'.join(path_parts[5:])  # Handle object keys with slashes
            self.handle_s3_object_delete(bucket_name, object_key)
        else:
            self.send_error(404, "Endpoint not found")

    def handle_s3_operations(self):
        try:
            # Get query parameters
            parsed_path = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_path.query)
            since_timestamp = query_params.get('since', [None])[0]

            # Get S3 operations using Python function
            operations_json = get_s3_operations(since_timestamp)

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(operations_json.encode())

        except Exception as e:
            self.send_error(500, f"Internal server error: {str(e)}")

    def handle_container_status(self, container_name):
        try:
            status = get_container_status(container_name)
            
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(status.encode())

        except Exception as e:
            self.send_error(500, f"Internal server error: {str(e)}")

    def handle_container_start(self, container_name):
        try:
            result = start_container(container_name)
            
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(result.encode())

        except Exception as e:
            self.send_error(500, f"Internal server error: {str(e)}")

    def handle_container_stop(self, container_name):
        try:
            result = stop_container(container_name)
            
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(result.encode())

        except Exception as e:
            self.send_error(500, f"Internal server error: {str(e)}")

    def handle_s3_object_create(self, bucket_name, object_key):
        try:
            # Get size parameter from query string
            parsed_path = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_path.query)
            size_kb = int(query_params.get('size_kb', [10])[0])
            
            result = create_bucket_object(bucket_name, object_key, size_kb)
            
            self.send_response(200 if result['success'] else 400)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        except Exception as e:
            self.send_error(500, f"Internal server error: {str(e)}")

    def handle_s3_object_read(self, bucket_name, object_key):
        try:
            result = read_bucket_object(bucket_name, object_key)
            
            self.send_response(200 if result['success'] else 404)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        except Exception as e:
            self.send_error(500, f"Internal server error: {str(e)}")

    def handle_s3_object_delete(self, bucket_name, object_key):
        try:
            result = delete_bucket_object(bucket_name, object_key)
            
            self.send_response(200 if result['success'] else 400)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        except Exception as e:
            self.send_error(500, f"Internal server error: {str(e)}")

    def handle_api_docs(self):
        try:
            # Check if this is a request for the OpenAPI spec
            if self.path.endswith('/openapi.json'):
                self.serve_openapi_spec()
                return

            # Serve Swagger UI
            swagger_html = """
<!DOCTYPE html>
<html>
<head>
    <title>SeaweedFS Cluster API - Swagger UI</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.10.3/swagger-ui.css" />
    <link rel="icon" type="image/png" href="https://unpkg.com/swagger-ui-dist@5.10.3/favicon-32x32.png" sizes="32x32" />
    <style>
        html {
            box-sizing: border-box;
            overflow: -moz-scrollbars-vertical;
            overflow-y: scroll;
        }
        *, *:before, *:after {
            box-sizing: inherit;
        }
        body {
            margin:0;
            background: #fafafa;
        }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.10.3/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@5.10.3/swagger-ui-standalone-preset.js"></script>
    <script>
    window.onload = function() {
        const ui = SwaggerUIBundle({
            url: '/api/docs/openapi.json',
            dom_id: '#swagger-ui',
            deepLinking: true,
            presets: [
                SwaggerUIBundle.presets.apis,
                SwaggerUIStandalonePreset
            ],
            plugins: [
                SwaggerUIBundle.plugins.DownloadUrl
            ],
            layout: "StandaloneLayout",
            tryItOutEnabled: true,
            requestInterceptor: (req) => {
                // Add any custom headers if needed
                return req;
            },
            responseInterceptor: (res) => {
                return res;
            }
        });
    };
    </script>
</body>
</html>
            """

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(swagger_html.encode())

        except Exception as e:
            self.send_error(500, f"Internal server error: {str(e)}")

    def serve_openapi_spec(self):
        """Serve the OpenAPI 3.0 specification"""
        try:
            # Get the original host from the request
            host = self.headers.get('Host', 'localhost:8080')
            protocol = 'http'  # Assuming HTTP for this demo, could be enhanced to detect HTTPS

            # Build dynamic server URLs
            base_url = f"{protocol}://{host}"
            api_base_url = f"{protocol}://{host.replace(':8080', ':9500')}/api"

            openapi_spec = {
                "openapi": "3.0.3",
                "info": {
                    "title": "SeaweedFS Cluster API",
                    "description": "API for managing SeaweedFS cluster containers and monitoring operations",
                    "version": "1.0.0",
                    "contact": {
                        "name": "SeaweedFS Cluster Admin",
                        "email": "admin@seaweedfs.local"
                    }
                },
                "servers": [
                    {
                        "url": base_url,
                        "description": "Direct API server"
                    },
                    {
                        "url": api_base_url,
                        "description": "API through nginx proxy"
                    }
                ],
                "paths": {
                    "/health": {
                        "get": {
                            "summary": "Health check (GET)",
                            "description": "Get detailed health status",
                            "responses": {
                                "200": {
                                    "description": "Health status",
                                    "content": {
                                        "application/json": {
                                            "schema": {
                                                "$ref": "#/components/schemas/HealthResponse"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "/containers/{containerName}": {
                        "get": {
                            "summary": "Get container status",
                            "description": "Get the current status of a specific container",
                            "parameters": [
                                {
                                    "name": "containerName",
                                    "in": "path",
                                    "required": True,
                                    "description": "Name of the container",
                                    "schema": {
                                        "type": "string",
                                        "enum": ["master1", "master2", "master3", "volume1", "volume2", "volume3", "filer1", "filer2", "nginx", "api"]
                                    }
                                }
                            ],
                            "responses": {
                                "200": {
                                    "description": "Container status",
                                    "content": {
                                        "text/plain": {
                                            "schema": {
                                                "type": "string",
                                                "enum": ["running", "stopped", "not_found"]
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "post": {
                            "summary": "Start container",
                            "description": "Start a specific container",
                            "parameters": [
                                {
                                    "name": "containerName",
                                    "in": "path",
                                    "required": True,
                                    "description": "Name of the container to start",
                                    "schema": {
                                        "type": "string",
                                        "enum": ["master1", "master2", "master3", "volume1", "volume2", "volume3", "filer1", "filer2", "nginx", "api"]
                                    }
                                }
                            ],
                            "responses": {
                                "200": {
                                    "description": "Container start result",
                                    "content": {
                                        "text/plain": {
                                            "schema": {
                                                "type": "string",
                                                "enum": ["started", "failed"]
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "delete": {
                            "summary": "Stop container",
                            "description": "Stop a specific container",
                            "parameters": [
                                {
                                    "name": "containerName",
                                    "in": "path",
                                    "required": True,
                                    "description": "Name of the container to stop",
                                    "schema": {
                                        "type": "string",
                                        "enum": ["master1", "master2", "master3", "volume1", "volume2", "volume3", "filer1", "filer2", "nginx", "api"]
                                    }
                                }
                            ],
                            "responses": {
                                "200": {
                                    "description": "Container stop result",
                                    "content": {
                                        "text/plain": {
                                            "schema": {
                                                "type": "string",
                                                "enum": ["stopped", "failed"]
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "/containers/{containerName}/health": {
                        "get": {
                            "summary": "Get container health",
                            "description": "Get detailed health status of a specific container",
                            "parameters": [
                                {
                                    "name": "containerName",
                                    "in": "path",
                                    "required": True,
                                    "description": "Name of the container",
                                    "schema": {
                                        "type": "string",
                                        "enum": ["master1", "master2", "master3", "volume1", "volume2", "volume3", "filer1", "filer2", "nginx", "api"]
                                    }
                                }
                            ],
                            "responses": {
                                "200": {
                                    "description": "Container health status",
                                    "content": {
                                        "application/json": {
                                            "schema": {
                                                "$ref": "#/components/schemas/ContainerHealthResponse"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "/s3-operations": {
                        "get": {
                            "summary": "Get S3 operations",
                            "description": "Get recent S3 operations performed on the cluster",
                            "parameters": [
                                {
                                    "name": "since",
                                    "in": "query",
                                    "required": False,
                                    "description": "Get operations since this timestamp (ISO format)",
                                    "schema": {
                                        "type": "string",
                                        "format": "date-time"
                                    }
                                }
                            ],
                            "responses": {
                                "200": {
                                    "description": "List of S3 operations",
                                    "content": {
                                        "application/json": {
                                            "schema": {
                                                "type": "array",
                                                "items": {
                                                    "$ref": "#/components/schemas/S3Operation"
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "/api/containers/{containerName}": {
                        "get": {
                            "summary": "Get container status (API prefix)",
                            "description": "Get the current status of a specific container using API prefix",
                            "parameters": [
                                {
                                    "name": "containerName",
                                    "in": "path",
                                    "required": True,
                                    "description": "Name of the container",
                                    "schema": {
                                        "type": "string",
                                        "enum": ["master1", "master2", "master3", "volume1", "volume2", "volume3", "filer1", "filer2", "nginx", "api"]
                                    }
                                }
                            ],
                            "responses": {
                                "200": {
                                    "description": "Container status",
                                    "content": {
                                        "text/plain": {
                                            "schema": {
                                                "type": "string",
                                                "enum": ["running", "stopped", "not_found"]
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "post": {
                            "summary": "Start container (API prefix)",
                            "description": "Start a specific container using API prefix",
                            "parameters": [
                                {
                                    "name": "containerName",
                                    "in": "path",
                                    "required": True,
                                    "description": "Name of the container to start",
                                    "schema": {
                                        "type": "string",
                                        "enum": ["master1", "master2", "master3", "volume1", "volume2", "volume3", "filer1", "filer2", "nginx", "api"]
                                    }
                                }
                            ],
                            "responses": {
                                "200": {
                                    "description": "Container start result",
                                    "content": {
                                        "text/plain": {
                                            "schema": {
                                                "type": "string",
                                                "enum": ["started", "failed"]
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "delete": {
                            "summary": "Stop container (API prefix)",
                            "description": "Stop a specific container using API prefix",
                            "parameters": [
                                {
                                    "name": "containerName",
                                    "in": "path",
                                    "required": True,
                                    "description": "Name of the container to stop",
                                    "schema": {
                                        "type": "string",
                                        "enum": ["master1", "master2", "master3", "volume1", "volume2", "volume3", "filer1", "filer2", "nginx", "api"]
                                    }
                                }
                            ],
                            "responses": {
                                "200": {
                                    "description": "Container stop result",
                                    "content": {
                                        "text/plain": {
                                            "schema": {
                                                "type": "string",
                                                "enum": ["stopped", "failed"]
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "/api/containers/{containerName}/health": {
                        "get": {
                            "summary": "Get container health (API prefix)",
                            "description": "Get detailed health status of a specific container using API prefix",
                            "parameters": [
                                {
                                    "name": "containerName",
                                    "in": "path",
                                    "required": True,
                                    "description": "Name of the container",
                                    "schema": {
                                        "type": "string",
                                        "enum": ["master1", "master2", "master3", "volume1", "volume2", "volume3", "filer1", "filer2", "nginx", "api"]
                                    }
                                }
                            ],
                            "responses": {
                                "200": {
                                    "description": "Container health status",
                                    "content": {
                                        "application/json": {
                                            "schema": {
                                                "$ref": "#/components/schemas/ContainerHealthResponse"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "components": {
                    "schemas": {
                        "HealthResponse": {
                            "type": "object",
                            "properties": {
                                "status": {
                                    "type": "string",
                                    "example": "healthy"
                                },
                                "service": {
                                    "type": "string",
                                    "example": "SeaweedFS Cluster API"
                                },
                                "timestamp": {
                                    "type": "string",
                                    "format": "date-time",
                                    "example": "2025-09-08T10:30:00.000Z"
                                }
                            }
                        },
                        "ContainerHealthResponse": {
                            "type": "object",
                            "properties": {
                                "status": {
                                    "type": "string",
                                    "enum": ["healthy", "unhealthy"],
                                    "example": "healthy"
                                },
                                "container": {
                                    "type": "string",
                                    "example": "master1"
                                }
                            }
                        },
                        "S3Operation": {
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "enum": ["GET", "PUT", "DELETE", "LIST"],
                                    "example": "GET"
                                },
                                "bucket": {
                                    "type": "string",
                                    "example": "user-uploads"
                                },
                                "object": {
                                    "type": "string",
                                    "example": "photos/vacation-2024/img_001.jpg"
                                },
                                "size": {
                                    "type": "string",
                                    "example": "15432KB"
                                },
                                "statusCode": {
                                    "type": "integer",
                                    "example": 200
                                },
                                "timestamp": {
                                    "type": "string",
                                    "format": "date-time",
                                    "example": "2025-09-08T10:30:00.000Z"
                                }
                            }
                        }
                    }
                }
            }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(openapi_spec).encode())

        except Exception as e:
            self.send_error(500, f"Internal server error: {str(e)}")

    def handle_container_health(self, container_name):
        try:
            health_status = check_container_health(container_name)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(f'{{"status": "{health_status}", "container": "{container_name}"}}'.encode())

        except Exception as e:
            self.send_error(500, f"Internal server error: {str(e)}")


# Helper functions for container management
def get_full_container_name(short_name):
    """Map short names to full Docker container names"""
    name_map = {
        'master1': 'seaweedfs-ha-demo-master1-1',
        'master2': 'seaweedfs-ha-demo-master2-1',
        'master3': 'seaweedfs-ha-demo-master3-1',
        'volume1': 'seaweedfs-ha-demo-volume1-1',
        'volume2': 'seaweedfs-ha-demo-volume2-1',
        'volume3': 'seaweedfs-ha-demo-volume3-1',
        'filer1': 'seaweedfs-ha-demo-filer1-1',
        'filer2': 'seaweedfs-ha-demo-filer2-1',
    }
    return name_map.get(short_name, short_name)


def get_container_status(short_name):
    """Get container status using Docker API"""
    container_name = get_full_container_name(short_name)
    
    try:
        # Use Docker socket to check container status
        req = urllib.request.Request(
            f"http://localhost/containers/{container_name}/json",
            method='GET'
        )
        
        # For Docker socket, we need to use a Unix socket connection
        # Since urllib doesn't support Unix sockets directly, we'll use curl via subprocess
        result = subprocess.run(
            ['curl', '-s', '--unix-socket', '/var/run/docker.sock', 
             f'http://localhost/containers/{container_name}/json'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout.strip():
            response_data = json.loads(result.stdout)
            if response_data.get('State', {}).get('Running', False):
                return 'running'
            else:
                return 'stopped'
        else:
            return 'not_found'
    except (subprocess.TimeoutExpired, json.JSONDecodeError, KeyError):
        return 'not_found'


def start_container(short_name):
    """Start container using Docker API"""
    container_name = get_full_container_name(short_name)
    
    try:
        result = subprocess.run(
            ['curl', '-s', '-X', 'POST', '--unix-socket', '/var/run/docker.sock',
             f'http://localhost/containers/{container_name}/start'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return 'started'
        else:
            return 'failed'
    except subprocess.TimeoutExpired:
        return 'failed'


def stop_container(short_name):
    """Stop container using Docker API"""
    container_name = get_full_container_name(short_name)
    
    try:
        result = subprocess.run(
            ['curl', '-s', '-X', 'POST', '--unix-socket', '/var/run/docker.sock',
             f'http://localhost/containers/{container_name}/stop'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return 'stopped'
        else:
            return 'failed'
    except subprocess.TimeoutExpired:
        return 'failed'


def check_container_health(short_name):
    """Check container health based on service type"""
    # First check if container is running
    status = get_container_status(short_name)
    if status != 'running':
        return 'unhealthy'
    
    # Check health based on service type
    try:
        if short_name.startswith('master'):
            # Check master health via cluster status endpoint
            req = urllib.request.Request(f"http://{short_name}:9333/cluster/status")
            with urllib.request.urlopen(req, timeout=5) as response:
                return 'healthy'
        elif short_name.startswith('volume'):
            # Check volume health via status endpoint
            req = urllib.request.Request(f"http://{short_name}:8080/status")
            with urllib.request.urlopen(req, timeout=5) as response:
                return 'healthy'
        elif short_name.startswith('filer'):
            # Check filer health via root endpoint
            req = urllib.request.Request(f"http://{short_name}:8888/")
            with urllib.request.urlopen(req, timeout=5) as response:
                return 'healthy'
        else:
            return 'unhealthy'
    except (urllib.error.URLError, urllib.error.HTTPError, OSError):
        return 'unhealthy'


def get_s3_client():
    """Create and return S3 client using environment variables"""
    return boto3.client(
        's3',
        endpoint_url=os.getenv('SEAWEED_S3_URL', 'http://localhost:9333'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name='us-east-1'  # SeaweedFS doesn't use regions, but boto3 requires it
    )


def generate_lorem_ipsum(size_kb=10):
    """Generate lorem ipsum text of approximately the specified size in KB"""
    lorem_base = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."
    
    # Calculate how many times to repeat to reach approximately size_kb
    base_size = len(lorem_base.encode('utf-8'))
    repetitions = max(1, (size_kb * 1024) // base_size)
    
    content = (lorem_base + " ") * repetitions
    return content[:size_kb * 1024]  # Trim to exact size


def create_bucket_object(bucket_name, object_key, size_kb=10):
    """Create a new object in the specified bucket with lorem ipsum content"""
    try:
        base_url = get_s3_base_url()
        
        # Generate lorem ipsum content
        content = generate_lorem_ipsum(size_kb)
        
        # Create bucket first (PUT request to bucket URL)
        bucket_url = f"{base_url}/{bucket_name}"
        requests.put(bucket_url)
        
        # Put object
        object_url = f"{bucket_url}/{object_key}"
        response = requests.put(object_url, data=content)
        
        if response.status_code in [200, 201]:
            return {
                "success": True,
                "message": f"Object '{object_key}' created in bucket '{bucket_name}'",
                "size": f"{len(content)} bytes"
            }
        else:
            return {
                "success": False,
                "message": f"Failed to create object: HTTP {response.status_code}",
                "size": "0 bytes"
            }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to create object: {str(e)}",
            "size": "0 bytes"
        }


def read_bucket_object(bucket_name, object_key):
    """Read an object from the specified bucket"""
    try:
        base_url = get_s3_base_url()
        
        object_url = f"{base_url}/{bucket_name}/{object_key}"
        response = requests.get(object_url)
        
        if response.status_code == 200:
            content = response.text
            return {
                "success": True,
                "content": content[:500] + "..." if len(content) > 500 else content,
                "size": f"{len(content)} bytes",
                "last_modified": response.headers.get('Last-Modified', 'Unknown')
            }
        else:
            return {
                "success": False,
                "content": "",
                "size": "0 bytes",
                "error": f"HTTP {response.status_code}: {response.text}"
            }
        
    except Exception as e:
        return {
            "success": False,
            "content": "",
            "size": "0 bytes",
            "error": str(e)
        }


def delete_bucket_object(bucket_name, object_key):
    """Delete an object from the specified bucket"""
    try:
        base_url = get_s3_base_url()
        
        object_url = f"{base_url}/{bucket_name}/{object_key}"
        response = requests.delete(object_url)
        
        if response.status_code in [200, 204]:
            return {
                "success": True,
                "message": f"Object '{object_key}' deleted from bucket '{bucket_name}'"
            }
        else:
            return {
                "success": False,
                "message": f"Failed to delete object: HTTP {response.status_code}"
            }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to delete object: {str(e)}"
        }


def get_s3_client():
    """Create and return S3 client using environment variables"""
    return boto3.client(
        's3',
        endpoint_url=os.getenv('SEAWEED_S3_URL', 'http://nginx:9333'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name='us-east-1'  # SeaweedFS doesn't use regions, but boto3 requires it
    )


def get_s3_base_url():
    """Get the base S3 URL for direct HTTP requests"""
    return os.getenv('SEAWEED_S3_URL', 'http://nginx:9333')


def get_s3_auth():
    """Get S3 authentication tuple"""
    return (os.getenv('AWS_ACCESS_KEY_ID'), os.getenv('AWS_SECRET_ACCESS_KEY'))


def get_s3_operations(since_timestamp=None):
    """Get actual S3 operations from SeaweedFS S3 API"""
    try:
        s3_client = get_s3_client()
        
        # List all buckets
        buckets = s3_client.list_buckets()
        operations = []
        
        for bucket in buckets['Buckets']:
            bucket_name = bucket['Name']
            
            try:
                # List objects in each bucket
                objects = s3_client.list_objects_v2(Bucket=bucket_name)
                
                if 'Contents' in objects:
                    for obj in objects['Contents']:
                        operations.append({
                            "type": "LIST",
                            "bucket": bucket_name,
                            "object": obj['Key'],
                            "size": f"{obj['Size']} bytes",
                            "statusCode": 200,
                            "timestamp": obj['LastModified'].strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                        })
                        
            except ClientError as e:
                # Bucket might be empty or inaccessible
                operations.append({
                    "type": "LIST",
                    "bucket": bucket_name,
                    "object": "",
                    "size": "",
                    "statusCode": 404 if e.response['Error']['Code'] == 'NoSuchBucket' else 500,
                    "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                })
        
        # If no buckets exist, return empty list
        if not operations:
            operations = [{
                "type": "INFO",
                "bucket": "",
                "object": "",
                "size": "",
                "statusCode": 200,
                "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            }]
            
        return json.dumps(operations)
        
    except Exception as e:
        # Return error information
        error_op = [{
            "type": "ERROR",
            "bucket": "",
            "object": "",
            "size": "",
            "statusCode": 500,
            "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        }]
        return json.dumps(error_op)


if __name__ == '__main__':
    PORT = 8080
    httpd = socketserver.TCPServer(("", PORT), ClusterAPIHandler)
    print("Cluster API server running on port %d" % PORT)
    httpd.serve_forever()
