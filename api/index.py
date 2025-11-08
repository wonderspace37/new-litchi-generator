import os
import sys
import json

# Add the api directory to the path for imports
sys.path.insert(0, os.path.dirname(__file__))

from waypoint_logic import generate_waypoints, export_to_litchi_csv, export_to_kml

def read_template():
    """Read the HTML template file."""
    template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return "<h1>Litchi Waypoint Generator API</h1><p>Template not found</p>"

def handler(req, res=None):
    """
    Vercel serverless function handler.
    Handles requests and routes them appropriately.
    Supports multiple request formats that Vercel might use.
    """
    try:
        # Extract request details - handle multiple formats
        method = 'GET'
        path = '/'
        headers = {}
        body = ''
        
        if isinstance(req, dict):
            # Dict format
            method = req.get('method', req.get('httpMethod', 'GET'))
            path = req.get('path', req.get('pathname', req.get('url', '/')))
            headers = req.get('headers', req.get('header', {}))
            body = req.get('body', req.get('payload', ''))
            # Handle query string in path
            if '?' in path:
                path = path.split('?')[0]
        elif hasattr(req, 'method'):
            # Object format with standard attributes
            method = getattr(req, 'method', 'GET')
            path = getattr(req, 'path', getattr(req, 'pathname', '/'))
            headers = getattr(req, 'headers', getattr(req, 'header', {}))
            body = getattr(req, 'body', getattr(req, 'payload', ''))
        else:
            # Try to get as attributes
            method = getattr(req, 'method', 'GET')
            path = getattr(req, 'path', '/')
            headers = getattr(req, 'headers', {})
            body = getattr(req, 'body', '')
        
        # Normalize path - remove query string and ensure it starts with /
        if path and '?' in path:
            path = path.split('?')[0]
        if not path or not path.startswith('/'):
            path = '/' + (path if path else '')
        
        # Handle root route - serve HTML template
        if path == '/' and method == 'GET':
            html_content = read_template()
            return {
                'statusCode': 200,
                'headers': {
                    'content-type': 'text/html; charset=utf-8'
                },
                'body': html_content
            }
        
        # Handle /generate route
        if path == '/generate' and method == 'POST':
            # Parse JSON body
            if isinstance(body, str):
                try:
                    data = json.loads(body)
                except json.JSONDecodeError:
                    return {
                        'statusCode': 400,
                        'headers': {'content-type': 'application/json'},
                        'body': json.dumps({'error': 'Invalid JSON'})
                    }
            else:
                data = body if isinstance(body, dict) else {}
            
            # Validate required fields
            try:
                init_lat = float(data["init_lat"])
                init_lon = float(data["init_lon"])
                init_bearing = float(data["init_bearing"])
                poi_altitude = float(data.get("poi_altitude", 1))
                fmt = data.get("format", "csv")
                waypoints = data["waypoints"]
            except (KeyError, ValueError, TypeError) as e:
                return {
                    'statusCode': 400,
                    'headers': {'content-type': 'application/json'},
                    'body': json.dumps({'error': f'Invalid request data: {str(e)}'})
                }
            
            # Generate waypoints
            try:
                results = generate_waypoints(init_lat, init_lon, init_bearing, waypoints)
            except Exception as e:
                return {
                    'statusCode': 500,
                    'headers': {'content-type': 'application/json'},
                    'body': json.dumps({'error': f'Error generating waypoints: {str(e)}'})
                }
            
            # Export to requested format
            try:
                if fmt == "kml":
                    filename = export_to_kml(init_lat, init_lon, results)
                    mime = "application/vnd.google-earth.kml+xml"
                    download = "litchi_path.kml"
                else:
                    filename = export_to_litchi_csv(
                        init_lat,
                        init_lon,
                        results,
                        poi_altitude,
                        speed=data.get("speed_start", 0),
                        curve=data.get("curve_size", 0),
                        pitch=data.get("gimbal_pitch", 0),
                        photo_interval=data.get("photo_interval", 1),
                    )
                    mime = "text/csv"
                    download = "litchi_waypoints.csv"
                
                # Read file content (CSV and KML are text files)
                with open(filename, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                
                # Clean up temp file
                try:
                    os.remove(filename)
                except Exception:
                    pass
                
                return {
                    'statusCode': 200,
                    'headers': {
                        'content-type': mime,
                        'content-disposition': f'attachment; filename="{download}"'
                    },
                    'body': file_content
                }
                
            except Exception as e:
                import traceback
                return {
                    'statusCode': 500,
                    'headers': {'content-type': 'application/json'},
                    'body': json.dumps({'error': f'Error exporting file: {str(e)}', 'traceback': traceback.format_exc()})
                }
        
        # 404 for other routes
        return {
            'statusCode': 404,
            'headers': {'content-type': 'application/json'},
            'body': json.dumps({'error': 'Not found'})
        }
        
    except Exception as e:
        import traceback
        return {
            'statusCode': 500,
            'headers': {'content-type': 'application/json'},
            'body': json.dumps({'error': str(e), 'traceback': traceback.format_exc()})
        }
