import os, sys, json
from flask import Flask, request, send_file, render_template
from waypoint_logic import generate_waypoints, export_to_litchi_csv, export_to_kml

# Ensure we can import waypoint_logic
sys.path.append(os.path.dirname(__file__))

app = Flask(
    __name__, template_folder=os.path.join(os.path.dirname(__file__), "../templates")
)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(force=True)
    init_lat = float(data["init_lat"])
    init_lon = float(data["init_lon"])
    init_bearing = float(data["init_bearing"])
    poi_altitude = float(data.get("poi_altitude", 1))
    speed = float(data.get("speed_start", 0))
    curve = float(data.get("curve_size", 0))
    pitch = float(data.get("gimbal_pitch", 0))
    photo_interval = float(data.get("photo_interval", 1))
    fmt = data.get("format", "csv").lower()

    waypoints = generate_waypoints(init_lat, init_lon, init_bearing, data["waypoints"])

    if fmt == "kml":
        filename = export_to_kml(init_lat, init_lon, waypoints)
        download_name = "waypoints.kml"
    else:
        filename = export_to_litchi_csv(
            init_lat,
            init_lon,
            waypoints,
            poi_altitude=poi_altitude,
            speed=speed,
            curve=curve,
            pitch=pitch,
            photo_interval=photo_interval,
            init_heading_deg=init_bearing,
        )
        download_name = "waypoints.csv"

    return send_file(filename, as_attachment=True, download_name=download_name)


# ✅ No app.run()
# ✅ Flask instance named 'app'
