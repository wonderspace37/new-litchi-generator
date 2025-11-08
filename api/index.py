from flask import Flask, request, send_file, render_template
from waypoint_logic import generate_waypoints, export_to_litchi_csv, export_to_kml
import os
#testing 
app = Flask(__name__, template_folder="templates")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(force=True)
    init_lat = float(data["init_lat"])
    init_lon = float(data["init_lon"])
    init_bearing = float(data["init_bearing"])
    poi_altitude = float(data.get("poi_altitude", 1))
    fmt = data.get("format", "csv")

    waypoints = data["waypoints"]
    results = generate_waypoints(init_lat, init_lon, init_bearing, waypoints)

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

    response = send_file(filename, mimetype=mime, as_attachment=True, download_name=download)
    
    # Clean up temp file after sending
    try:
        os.remove(filename)
    except Exception:
        pass

    return response

# Export for Vercel
handler = app
