#!/usr/bin/env python3
"""
Jinja2 Template Renderer for SeaweedFS Node Pages
"""

import os
import json
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

class NodeTemplateRenderer:
    def __init__(self, template_dir="templates", output_dir="html"):
        self.template_dir = Path(template_dir)
        self.output_dir = Path(output_dir)
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def render_filer_template(self, filer_num):
        """Render filer template with specific data"""
        template = self.env.get_template('base_node.html')

        # Define filer-specific data
        data = {
            'page_title': f'Filer {filer_num} & S3 Node {filer_num} Details - SeaweedFS',
            'node_title': f'Filer {filer_num} & S3 Node {filer_num} Details',
            'node_type': 'Filer & S3 Node',
            'node_description': 'Data Center: dc1, Running since: <span id="uptime">Loading...</span>',
            'status_items': {
                'HTTP Port': '8888',
                'gRPC Port': '18888',
                'S3 Port': '8333',
                'Max Memory': '1024 MB'
            },
            'connected_components': [
                {'name': 'Master 1', 'path': '/master/1/'},
                {'name': 'Master 2', 'path': '/master/2/'},
                {'name': 'Master 3', 'path': '/master/3/'}
            ],
            'storage_stats': {
                'Total Files': {'id': 'total-files', 'default': 'Loading...'},
                'Total Directories': {'id': 'total-dirs', 'default': 'Loading...'},
                'Used Space': {'id': 'used-space', 'default': 'Loading...'},
                'Free Space': {'id': 'free-space', 'default': 'Loading...'}
            },
            'storage_usage_bar': True,
            's3_stats': {
                'Total Buckets': {'id': 'total-buckets', 'default': '0'},
                'Total Objects': {'id': 'total-objects', 'default': '0'},
                'Storage Used': {'id': 's3-storage-used', 'default': '0 MB'},
                'Requests/min': {'id': 'requests-per-min', 'default': '0'}
            },
            'operations_title': 'Recent S3 Operations',
            'operations': {
                'PUT Operations': {'id': 'recent-put', 'default': '0'},
                'GET Operations': {'id': 'recent-get', 'default': '0'},
                'DELETE Operations': {'id': 'recent-delete', 'default': '0'},
                'LIST Operations': {'id': 'recent-list', 'default': '0'}
            },
            'api_links': [
                {'url': f'/filer/{filer_num}/', 'text': 'Filer Web Interface'},
                {'url': f'/filer/{filer_num}/?path=/', 'text': 'Browse Root Directory'},
                {'url': f'/filer/{filer_num}/admin/master/status', 'text': 'Master Status'},
                {'url': f'/filer/{filer_num}/admin/cluster/status', 'text': 'Cluster Status'}
            ],
            'custom_js': '''
        function updateStats() {
            document.getElementById('total-files').textContent = Math.floor(Math.random() * 1000) + ' files';
            document.getElementById('total-dirs').textContent = Math.floor(Math.random() * 100) + ' directories';
            document.getElementById('used-space').textContent = Math.floor(Math.random() * 500) + ' MB';
            document.getElementById('free-space').textContent = Math.floor(Math.random() * 500) + ' MB';

            const usagePercent = Math.floor(Math.random() * 80) + 10;
            document.getElementById('storage-usage-bar').style.width = usagePercent + '%';
            document.getElementById('storage-usage-bar').textContent = usagePercent + '%';

            document.getElementById('total-buckets').textContent = Math.floor(Math.random() * 20) + 5;
            document.getElementById('total-objects').textContent = Math.floor(Math.random() * 10000) + 1000;
            document.getElementById('s3-storage-used').textContent = Math.floor(Math.random() * 2000) + 500 + ' MB';
            document.getElementById('requests-per-min').textContent = Math.floor(Math.random() * 100) + 10;

            document.getElementById('recent-put').textContent = Math.floor(Math.random() * 20) + 5;
            document.getElementById('recent-get').textContent = Math.floor(Math.random() * 50) + 10;
            document.getElementById('recent-delete').textContent = Math.floor(Math.random() * 5) + 1;
            document.getElementById('recent-list').textContent = Math.floor(Math.random() * 30) + 5;
        }
            '''
        }

        return template.render(**data)

    def render_volume_template(self, volume_num):
        """Render volume template with specific data"""
        template = self.env.get_template('base_node.html')

        data = {
            'page_title': f'Volume {volume_num} Details - SeaweedFS',
            'node_title': f'Volume {volume_num} Details',
            'node_type': 'Volume Server',
            'node_description': f'Data Center: dc1, Volume server {volume_num} for data storage',
            'status_items': {
                'Volume Port': '8080',
                'Max Volumes': '100',
                'Data Directory': f'/data/volume{volume_num}',
                'Replication': '001'
            },
            'connected_components': [
                {'name': 'Master 1', 'path': '/master/1/'},
                {'name': 'Master 2', 'path': '/master/2/'},
                {'name': 'Master 3', 'path': '/master/3/'}
            ],
            'storage_stats': {
                'Total Volumes': {'id': 'total-volumes', 'default': 'Loading...'},
                'Used Space': {'id': 'used-space', 'default': 'Loading...'},
                'Free Space': {'id': 'free-space', 'default': 'Loading...'},
                'Active Writes': {'id': 'active-writes', 'default': 'Loading...'}
            },
            'storage_usage_bar': True,
            'operations': {
                'Read Operations': {'id': 'read-ops', 'default': '0'},
                'Write Operations': {'id': 'write-ops', 'default': '0'},
                'Delete Operations': {'id': 'delete-ops', 'default': '0'}
            },
            'api_links': [
                {'url': f'/volume/{volume_num}/status', 'text': 'Volume Status'},
                {'url': f'/volume/{volume_num}/', 'text': 'Volume API'}
            ],
            'custom_js': '''
        function updateStats() {
            document.getElementById('total-volumes').textContent = Math.floor(Math.random() * 50) + 10;
            document.getElementById('used-space').textContent = Math.floor(Math.random() * 1000) + 100 + ' GB';
            document.getElementById('free-space').textContent = Math.floor(Math.random() * 500) + 50 + ' GB';
            document.getElementById('active-writes').textContent = Math.floor(Math.random() * 20);

            const usagePercent = Math.floor(Math.random() * 80) + 10;
            document.getElementById('storage-usage-bar').style.width = usagePercent + '%';
            document.getElementById('storage-usage-bar').textContent = usagePercent + '%';

            document.getElementById('read-ops').textContent = Math.floor(Math.random() * 1000) + 100;
            document.getElementById('write-ops').textContent = Math.floor(Math.random() * 500) + 50;
            document.getElementById('delete-ops').textContent = Math.floor(Math.random() * 50) + 5;
        }
            '''
        }

        return template.render(**data)

    def render_master_template(self, master_num):
        """Render master template with specific data"""
        template = self.env.get_template('base_node.html')

        is_leader = master_num == 1  # Master 1 is the leader

        data = {
            'page_title': f'Master {master_num} Details - SeaweedFS',
            'node_title': f'Master {master_num} Details',
            'node_type': 'Master Server',
            'node_description': f'Data Center: dc1, Raft cluster member {master_num}{" (Leader)" if is_leader else ""}',
            'status_items': {
                'Master Port': '9333',
                'Raft Port': '19333',
                'Data Directory': f'/data/master{master_num}',
                'Cluster Size': '3'
            },
            'connected_components': [
                {'name': 'Master 1', 'path': '/master/1/'},
                {'name': 'Master 2', 'path': '/master/2/'},
                {'name': 'Master 3', 'path': '/master/3/'}
            ],
            'operations': {
                'Total Allocations': {'id': 'total-allocations', 'default': '0'},
                'Active Volumes': {'id': 'active-volumes', 'default': '0'},
                'Raft Commits': {'id': 'raft-commits', 'default': '0'},
                'Leader Changes': {'id': 'leader-changes', 'default': '0'}
            },
            'api_links': [
                {'url': f'/master/{master_num}/', 'text': 'Master Web Interface'},
                {'url': f'/master/{master_num}/cluster/status', 'text': 'Cluster Status'},
                {'url': f'/master/{master_num}/dir/status', 'text': 'Directory Status'}
            ],
            'custom_js': f'''
        function updateStats() {{
            document.getElementById('total-allocations').textContent = Math.floor(Math.random() * 10000) + 1000;
            document.getElementById('active-volumes').textContent = Math.floor(Math.random() * 100) + 20;
            document.getElementById('raft-commits').textContent = Math.floor(Math.random() * 1000) + 100;
            document.getElementById('leader-changes').textContent = Math.floor(Math.random() * 10);
        }}
            '''
        }

        return template.render(**data)

    def save_template(self, content, filename):
        """Save rendered template to file"""
        output_path = self.output_dir / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"Generated: {output_path}")

    def generate_all_templates(self):
        """Generate all node templates"""
        # Generate filer templates
        for i in [1, 2]:
            content = self.render_filer_template(i)
            self.save_template(content, f'filer/filer{i}.html')

        # Generate volume templates
        for i in [1, 2, 3]:
            content = self.render_volume_template(i)
            self.save_template(content, f'volume/volume{i}.html')

        # Generate master templates
        for i in [1, 2, 3]:
            content = self.render_master_template(i)
            self.save_template(content, f'master/master{i}.html')

def main():
    renderer = NodeTemplateRenderer()
    renderer.generate_all_templates()
    print("All templates generated successfully!")

if __name__ == "__main__":
    main()
