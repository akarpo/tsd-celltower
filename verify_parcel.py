#!/usr/bin/env python3
"""
Verify a metes-and-bounds legal description against the Oakland County parcel
of record, and visualize both over satellite imagery.

Parcel 88-20-20-100-003 (OC KEYPIN 2020100003), 3570 Northfield Pkwy, Troy MI.
Legal description as supplied:

  T2N, R11E, SEC 20, PART OF SE 1/4 OF NW 1/4
  BEG AT PT DIST N 00-09-00 W 210.40 FT FROM CEN OF SEC
  TH S 89-18-04 W 620.03 FT
  TH N 00-09-00 W 1127.10 FT
  TH N 89-51-00 E 620.00 FT
  TH S 00-09-00 E 1121.00 FT TO BEG          -- 16 A

Method: trace the traverse in local feet (origin = Center of Section), then
georeference by anchoring the Point of Beginning onto the official parcel's
surveyed SE corner with +Y = true north (PLSS section calls are referenced to
true north). The other three corners then fall where the calls put them --
if the description matches the parcel, they land on the official corners.

Outputs (next to this script):
  parcel_verification.geojson  -- both polygons + points
  parcel_verification.html     -- interactive Leaflet map over Esri imagery
"""
import json
import math
import os

import requests

# ---------------------------------------------------------------- inputs ---
# Each call: (NS, deg, min, sec, EW, distance_ft)
POB_FROM_CENTER = ("N", 0, 9, 0, "W", 210.40)      # BEG, measured from CEN OF SEC
LEGS = [
    ("S", 89, 18,  4, "W",  620.03),
    ("N",  0,  9,  0, "W", 1127.10),
    ("N", 89, 51,  0, "E",  620.00),
    ("S",  0,  9,  0, "E", 1121.00),               # ...TO BEG
]
TOWER = (42.571750, -83.177833)   # 42 34 18.3 N, 83 10 40.2 W -- user-supplied, inspected on site
KEYPIN = "2020100003"
PARCEL_REST = ("https://gisservices.oakgov.com/arcgis/rest/services/Enterprise/"
               "EnterpriseOpenParcelDataMapService/MapServer/1/query")
HERE = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------- traverse ----
def azimuth(ns, d, m, s, ew):
    """Quadrant bearing -> azimuth in radians, clockwise from true north."""
    ang = d + m / 60 + s / 3600
    az = {("N", "E"): ang, ("S", "E"): 180 - ang,
          ("S", "W"): 180 + ang, ("N", "W"): 360 - ang}[(ns, ew)]
    return math.radians(az)

def delta(call):
    *bearing, dist = call
    az = azimuth(*bearing)
    return dist * math.sin(az), dist * math.cos(az)   # (east_ft, north_ft)

# Local feet coordinates, origin = CEN OF SEC, +x East, +y North.
beg = delta(POB_FROM_CENTER)
local = [beg]
x, y = beg
for leg in LEGS:
    dx, dy = delta(leg)
    x, y = x + dx, y + dy
    local.append((x, y))
misclosure_ft = math.hypot(local[-1][0] - local[0][0], local[-1][1] - local[0][1])
corners_local = local[:-1]            # BEG, P2, P3, P4

def shoelace(pts):
    a = sum(pts[i][0] * pts[(i + 1) % len(pts)][1]
            - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))
    return abs(a) / 2

legal_area_ac = shoelace(corners_local) / 43560.0

# --------------------------------------------------- official parcel -------
print(f"Fetching official parcel {KEYPIN} from Oakland County GIS...")
resp = requests.get(PARCEL_REST, params={
    "where": f"KEYPIN='{KEYPIN}'", "outFields": "*",
    "returnGeometry": "true", "outSR": "4326", "f": "geojson",
}, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
resp.raise_for_status()
official = resp.json()["features"][0]
off_ring = official["geometry"]["coordinates"][0]          # [ [lon,lat], ... ]
off_props = official["properties"]

lats = [p[1] for p in off_ring]
lons = [p[0] for p in off_ring]
bbox = dict(minlat=min(lats), maxlat=max(lats), minlon=min(lons), maxlon=max(lons))

def nearest_vertex(target_lat, target_lon):
    return min(off_ring, key=lambda p: (p[1] - target_lat) ** 2 + (p[0] - target_lon) ** 2)

off_corners = {                                            # (lon, lat)
    "SE": nearest_vertex(bbox["minlat"], bbox["maxlon"]),
    "SW": nearest_vertex(bbox["minlat"], bbox["minlon"]),
    "NW": nearest_vertex(bbox["maxlat"], bbox["minlon"]),
    "NE": nearest_vertex(bbox["maxlat"], bbox["maxlon"]),
}

# ------------------------------------------------- georeference ------------
# Anchor: BEG (corners_local[0]) -> official surveyed SE corner.
se_lon, se_lat = off_corners["SE"]
phi = math.radians(se_lat)
ft_per_deg_lat = (111132.92 - 559.82 * math.cos(2 * phi) + 1.175 * math.cos(4 * phi)
                  - 0.0023 * math.cos(6 * phi)) * 3.280839895
ft_per_deg_lon = (111412.84 * math.cos(phi) - 93.5 * math.cos(3 * phi)
                  + 0.118 * math.cos(5 * phi)) * 3.280839895
bx, by = corners_local[0]

def local_to_latlon(x, y):
    return (se_lat + (y - by) / ft_per_deg_lat,
            se_lon + (x - bx) / ft_per_deg_lon)

legal_latlon = [local_to_latlon(x, y) for x, y in corners_local]   # (lat, lon)
center_latlon = local_to_latlon(0.0, 0.0)                          # CEN OF SEC

def dist_ft(a_lat, a_lon, b_lat, b_lon):
    return math.hypot((a_lat - b_lat) * ft_per_deg_lat,
                      (a_lon - b_lon) * ft_per_deg_lon)

# Corner-by-corner agreement: legal P2/P3/P4 vs official SW/NW/NE.
labels = ["BEG/SE", "P2/SW", "P3/NW", "P4/NE"]
off_order = ["SE", "SW", "NW", "NE"]
corner_dev = []
for lbl, (la, lo), oc in zip(labels, legal_latlon, off_order):
    olon, olat = off_corners[oc]
    corner_dev.append((lbl, dist_ft(la, lo, olat, olon)))

# Official parcel area from its own geometry (sanity check vs the legal "16 A").
off_xy = [( (lon - se_lon) * ft_per_deg_lon, (lat - se_lat) * ft_per_deg_lat )
          for lon, lat in off_ring]
official_area_ac = shoelace(off_xy[:-1] if off_xy[0] == off_xy[-1] else off_xy) / 43560.0

def point_in_ring(lat, lon, ring_latlon):
    inside = False
    n = len(ring_latlon)
    for i in range(n):
        y1, x1 = ring_latlon[i]
        y2, x2 = ring_latlon[(i + 1) % n]
        if (y1 > lat) != (y2 > lat):
            xint = x1 + (lat - y1) / (y2 - y1) * (x2 - x1)
            if lon < xint:
                inside = not inside
    return inside

off_ring_latlon = [(p[1], p[0]) for p in off_ring]
tower_in_legal = point_in_ring(TOWER[0], TOWER[1], legal_latlon)
tower_in_official = point_in_ring(TOWER[0], TOWER[1], off_ring_latlon)

# ------------------------------------------------- write GeoJSON -----------
def ring(coords_latlon):                       # -> GeoJSON [lon,lat] closed ring
    r = [[lon, lat] for lat, lon in coords_latlon]
    r.append(r[0])
    return r

geo = {"type": "FeatureCollection", "features": [
    {"type": "Feature",
     "properties": {"name": "Official parcel (Oakland County)", "kind": "official",
                    "keypin": KEYPIN, "site": off_props.get("SITEADDRESS"),
                    "area_acres": round(official_area_ac, 3)},
     "geometry": {"type": "Polygon", "coordinates": [[[p[0], p[1]] for p in off_ring]]}},
    {"type": "Feature",
     "properties": {"name": "Legal description (reconstructed)", "kind": "legal",
                    "area_acres": round(legal_area_ac, 3),
                    "misclosure_ft": round(misclosure_ft, 3)},
     "geometry": {"type": "Polygon", "coordinates": [ring(legal_latlon)]}},
    {"type": "Feature",
     "properties": {"name": "AT&T cell tower (inspected on site)", "kind": "tower"},
     "geometry": {"type": "Point", "coordinates": [TOWER[1], TOWER[0]]}},
    {"type": "Feature",
     "properties": {"name": "Center of Section 20 (derived)", "kind": "center"},
     "geometry": {"type": "Point", "coordinates": [center_latlon[1], center_latlon[0]]}},
    {"type": "Feature",
     "properties": {"name": "Point of Beginning", "kind": "pob"},
     "geometry": {"type": "Point", "coordinates": [legal_latlon[0][1], legal_latlon[0][0]]}},
]}
geojson_path = os.path.join(HERE, "parcel_verification.geojson")
with open(geojson_path, "w") as f:
    json.dump(geo, f, indent=2)

# ------------------------------------------------- write Leaflet HTML ------
all_lat = lats + [c[0] for c in legal_latlon] + [TOWER[0]]
all_lon = lons + [c[1] for c in legal_latlon] + [TOWER[1]]
bounds = [[min(all_lat), min(all_lon)], [max(all_lat), max(all_lon)]]

html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Parcel verification - {KEYPIN}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  html,body,#map{{height:100%;margin:0}}
  .legend{{background:#fff;padding:10px 12px;font:13px/1.4 system-ui,sans-serif;
    box-shadow:0 1px 5px rgba(0,0,0,.4);border-radius:6px;max-width:300px}}
  .legend b{{font-size:13px}} .sw{{display:inline-block;width:14px;height:14px;
    vertical-align:-2px;margin-right:6px;border:1px solid #333}}
</style></head><body><div id="map"></div><script>
var map = L.map('map');
L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}',
  {{maxZoom:21, attribution:'Esri World Imagery'}}).addTo(map);
var data = {json.dumps(geo)};
function style(f){{
  if(f.properties.kind==='official') return {{color:'#1e90ff',weight:3,fill:false}};
  if(f.properties.kind==='legal')    return {{color:'#ff7f0e',weight:2,fillColor:'#ff7f0e',fillOpacity:0.35}};
}}
L.geoJSON(data,{{
  filter:f=>f.geometry.type==='Polygon',
  style:style,
  onEachFeature:(f,l)=>l.bindPopup('<b>'+f.properties.name+'</b>'+
    (f.properties.area_acres?'<br>area: '+f.properties.area_acres+' ac':''))
}}).addTo(map);
var icons={{tower:'#e6194b',center:'#911eb4',pob:'#3cb44b'}};
L.geoJSON(data,{{
  filter:f=>f.geometry.type==='Point',
  pointToLayer:(f,ll)=>L.circleMarker(ll,{{radius:f.properties.kind==='tower'?8:6,
    color:'#fff',weight:2,fillColor:icons[f.properties.kind],fillOpacity:1}}),
  onEachFeature:(f,l)=>l.bindPopup('<b>'+f.properties.name+'</b>')
}}).addTo(map);
map.fitBounds({json.dumps(bounds)},{{padding:[40,40]}});
var lg=L.control({{position:'topright'}});
lg.onAdd=function(){{var d=L.DomUtil.create('div','legend');d.innerHTML=
  '<b>Parcel {KEYPIN} &mdash; 3570 Northfield Pkwy</b><br>'+
  '<span class=sw style="background:#ff7f0e"></span>Legal description (reconstructed) &mdash; {legal_area_ac:.2f} ac<br>'+
  '<span class=sw style="background:#1e90ff;opacity:.6"></span>Official Oakland County parcel &mdash; {official_area_ac:.2f} ac<br>'+
  '<span class=sw style="background:#e6194b;border-radius:50%"></span>AT&amp;T tower (on-site coords)<br>'+
  '<span class=sw style="background:#3cb44b;border-radius:50%"></span>Point of Beginning<br>'+
  '<span class=sw style="background:#911eb4;border-radius:50%"></span>Center of Section 20 (derived)<br>'+
  '<small>Tower inside legal-description polygon: <b>{ "YES" if tower_in_legal else "NO" }</b></small>';
  return d;}};
lg.addTo(map);
</script></body></html>"""
html_path = os.path.join(HERE, "parcel_verification.html")
with open(html_path, "w") as f:
    f.write(html)

# ------------------------------------------------------- report -----------
print(f"""
=================  LEGAL DESCRIPTION  vs  PARCEL OF RECORD  =================
Traverse misclosure ........ {misclosure_ft:.2f} ft  (internal consistency of the calls)
Legal-description area ..... {legal_area_ac:.2f} acres   (description states "16 A")
Official parcel area ....... {official_area_ac:.2f} acres   (OC Shape.area = {off_props.get('Shape.area', 'n/a')})
Site address ............... {off_props.get('SITEADDRESS')}, {off_props.get('SITECITY')}
Owner mailing address ...... {off_props.get('POSTALADDRESS')}
Assessed / taxable value ... {off_props.get('ASSESSEDVALUE')} / {off_props.get('TAXABLEVALUE')}  (0 = tax-exempt)

Corner agreement (POB anchored to official SE corner, +Y = true north):""")
for lbl, dev in corner_dev:
    print(f"  {lbl:8s} legal corner lands {dev:6.1f} ft from official corner")
print(f"""
Derived Center of Section 20 ... {center_latlon[0]:.6f}, {center_latlon[1]:.6f}
AT&T tower {TOWER[0]}, {TOWER[1]}
  inside legal-description polygon ... {tower_in_legal}
  inside official parcel polygon ..... {tower_in_official}

Wrote: {os.path.relpath(html_path)}
       {os.path.relpath(geojson_path)}
============================================================================""")
