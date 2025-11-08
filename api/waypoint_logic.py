import csv
import math
import os
import tempfile

EARTH_RADIUS = 6378137.0  # meters

def destination_point(lat, lon, bearing, distance_m):
    """Project from (lat, lon) by distance_m along bearing (deg)."""
    lat1 = math.radians(lat)
    lon1 = math.radians(lon)
    brg = math.radians(bearing)
    d_div_r = distance_m / EARTH_RADIUS

    lat2 = math.asin(
        math.sin(lat1) * math.cos(d_div_r)
        + math.cos(lat1) * math.sin(d_div_r) * math.cos(brg)
    )
    lon2 = lon1 + math.atan2(
        math.sin(brg) * math.sin(d_div_r) * math.cos(lat1),
        math.cos(d_div_r) - math.sin(lat1) * math.sin(lat2),
    )
    return math.degrees(lat2), math.degrees(lon2)

def generate_waypoints(init_lat, init_lon, init_bearing, waypoints):
    """Generate relative GPS waypoints from input JSON data."""
    results = []
    curr_lat, curr_lon = init_lat, init_lon
    for wp in waypoints:
        horiz = float(wp.get("horizontal", 0.0))
        vert = float(wp.get("vertical", 2.0))
        bearing = (float(init_bearing) + float(wp.get("bearing", 0.0))) % 360.0
        hold = float(wp.get("hold_time", 0.0))

        lat2, lon2 = destination_point(curr_lat, curr_lon, bearing, horiz)
        results.append({
            "latitude": lat2,
            "longitude": lon2,
            "altitude": max(2.0, vert),
            "true_bearing": bearing,
            "hold_time": hold,
        })
        curr_lat, curr_lon = lat2, lon2
    return results

def _safe_tmp_path(suffix):
    """Create a temp file path under /tmp (Vercel safe)."""
    fd, path = tempfile.mkstemp(suffix=suffix, dir="/tmp")
    os.close(fd)
    return path

def export_to_litchi_csv(
    init_lat, init_lon, waypoints, poi_altitude=1,
    speed=0, curve=0, pitch=0, photo_interval=1, init_heading_deg=0,
):
    """Generate a Litchi-compatible CSV file."""
    filename = _safe_tmp_path(".csv")
    headers = [
        "latitude","longitude","altitude(m)","heading(deg)","curvesize(m)","rotationdir",
        "gimbalmode","gimbalpitchangle","actiontype1","actionparam1","altitudemode",
        "speed(m/s)","poi_latitude","poi_longitude","poi_altitude(m)",
        "poi_altitudemode","photo_timeinterval","photo_distinterval",
    ]
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        # WP0 (home)
        writer.writerow({
            "latitude": init_lat,"longitude": init_lon,"altitude(m)": 5,
            "heading(deg)": float(init_heading_deg),"curvesize(m)": float(curve),
            "rotationdir": 0,"gimbalmode": 0,"gimbalpitchangle": float(pitch),
            "actiontype1": 0,"actionparam1": 0,"altitudemode": 0,
            "speed(m/s)": float(speed),"poi_latitude": init_lat,"poi_longitude": init_lon,
            "poi_altitude(m)": float(poi_altitude),"poi_altitudemode": 0,
            "photo_timeinterval": float(photo_interval),"photo_distinterval": 0,
        })
        # WP1+
        for wp in waypoints:
            writer.writerow({
                "latitude": wp["latitude"],"longitude": wp["longitude"],
                "altitude(m)": wp["altitude"],"heading(deg)": wp["true_bearing"],
                "curvesize(m)": float(curve),"rotationdir": 0,"gimbalmode": 0,
                "gimbalpitchangle": float(pitch),"actiontype1": 0,
                "actionparam1": int(float(wp.get("hold_time", 0)) * 1000),
                "altitudemode": 0,"speed(m/s)": float(speed),
                "poi_latitude": init_lat,"poi_longitude": init_lon,
                "poi_altitude(m)": float(poi_altitude),"poi_altitudemode": 0,
                "photo_timeinterval": float(photo_interval),"photo_distinterval": 0,
            })
    return filename

def export_to_kml(init_lat, init_lon, waypoints):
    """Generate a simple KML path for visualization."""
    filename = _safe_tmp_path(".kml")
    with open(filename, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
        f.write("  <Document>\n")
        f.write("    <name>Waypoint Path</name>\n")
        f.write("    <Placemark>\n")
        f.write("      <name>Flight Path</name>\n")
        f.write(
            "      <Style><LineStyle><color>ff3b82f6</color><width>3</width></LineStyle></Style>\n"
        )
        f.write("      <LineString>\n")
        f.write("        <tessellate>1</tessellate>\n")
        f.write("        <altitudeMode>absolute</altitudeMode>\n")
        f.write("        <coordinates>\n")
        f.write(f"          {init_lon},{init_lat},5\n")
        for wp in waypoints:
            f.write(f'          {wp["longitude"]},{wp["latitude"]},{wp["altitude"]}\n')
        f.write("        </coordinates>\n")
        f.write("      </LineString>\n")
        f.write("    </Placemark>\n")
        f.write("  </Document>\n")
        f.write("</kml>\n")
    return filename
