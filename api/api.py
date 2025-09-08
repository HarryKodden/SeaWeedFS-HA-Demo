#!/usr/bin/env python3

import http.server
import socketserver
import subprocess
import json
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timezone
import base64
import time

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


def get_s3_operations(since_timestamp=None):
    """Get S3 operations (mock data for demo)"""
    current_time = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    
    # Mock S3 operations data
    operations = [
        {
            "type": "GET",
            "bucket": "user-uploads",
            "object": "photos/vacation-2024/img_001.jpg",
            "size": "",
            "statusCode": 200,
            "timestamp": current_time
        },
        {
            "type": "PUT", 
            "bucket": "backups",
            "object": "database/daily_backup.sql.gz",
            "size": "15432KB",
            "statusCode": 200,
            "timestamp": current_time
        },
        {
            "type": "LIST",
            "bucket": "documents",
            "object": "reports/",
            "size": "",
            "statusCode": 200,
            "timestamp": current_time
        }
    ]
    
    return json.dumps(operations)


if __name__ == '__main__':
    PORT = 8080
    httpd = socketserver.TCPServer(("", PORT), ClusterAPIHandler)
    print("Cluster API server running on port %d" % PORT)
    httpd.serve_forever()
