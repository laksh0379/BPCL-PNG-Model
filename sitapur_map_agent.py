#!/usr/bin/env python3
"""
Sitapur Area Polygon Mapping Agent
- All 40 sub-area coordinates hardcoded (no CSV needed)
- Fetches OSM boundary polygons from Nominatim
- Falls back to radius circles if polygon not found
- Renders on ESRI Satellite + CartoDB labels
- Outputs sitapur_map.html and auto-opens it
"""

import requests, json, time, math, webbrowser, pathlib, sys
from collections import defaultdict

OUTPUT_HTML = "sitapur_map.html"

# ─── ALL 40 AREAS HARDCODED ───
# (MRU, Main_Area, Subarea, Lat, Lon, Status)
AREAS = [
    # ── MRU-1 | Naipalapur ──
    ("MRU-1","Naipalapur","Adarsh Nagar",      27.570658, 80.705658, "VERIFIED"),
    ("MRU-1","Naipalapur","Anand Nagar",        27.565406, 80.698234, "HIGH_SPREAD"),
    ("MRU-1","Naipalapur","Bhawanpurva",        27.563448, 80.699677, "HIGH_SPREAD"),
    ("MRU-1","Naipalapur","Naipalapur",         27.569612, 80.707943, "VERIFIED"),
    ("MRU-1","Naipalapur","Rampurva",           27.571666, 80.711863, "VERIFIED_10X"),
    ("MRU-1","Naipalapur","Rasoolganj",         27.565058, 80.685057, "HIGH_SPREAD"),
    ("MRU-1","Naipalapur","Sheeshmahal",        27.566405, 80.704909, "VERIFIED"),

    # ── MRU-2 | Panchampurva ──
    ("MRU-2","Panchampurva","Panchampurva",     27.574500, 80.697745, "VERIFIED_10X"),
    ("MRU-2","Panchampurva","Guru Nanak Colony",27.568539, 80.694437, "VERIFIED"),
    ("MRU-2","Panchampurva","Gwal Mandi",       27.569887, 80.695104, "HIGH_SPREAD"),
    ("MRU-2","Panchampurva","Subhash Nagar",    27.565498, 80.696172, "HIGH_SPREAD"),

    # ── MRU-5 | Lohar Bagh ──
    ("MRU-5","Lohar Bagh","Agha Colony",        27.567920, 80.669094, "VERIFIED"),
    ("MRU-5","Lohar Bagh","Arya Nagar",         27.561750, 80.684590, "VERIFIED"),
    ("MRU-5","Lohar Bagh","Awas Vikas Block A", 27.556362, 80.695399, "VERIFIED"),
    ("MRU-5","Lohar Bagh","Awas Vikas Block C", 27.557036, 80.694145, "VERIFIED"),
    ("MRU-5","Lohar Bagh","Baijnath Colony",    27.565760, 80.662577, "HIGH_SPREAD"),
    ("MRU-5","Lohar Bagh","Chitra Colony",      27.534327, 80.678973, "HIGH_SPREAD"),
    ("MRU-5","Lohar Bagh","Civil Lines",        27.565208, 80.677026, "VERIFIED"),
    ("MRU-5","Lohar Bagh","Ghuramau Bangla",    27.561129, 80.679560, "VERIFIED"),
    ("MRU-5","Lohar Bagh","Kathalibagh",        27.563448, 80.680601, "HIGH_SPREAD"),
    ("MRU-5","Lohar Bagh","Lohar Bagh",         27.564353, 80.680572, "VERIFIED"),
    ("MRU-5","Lohar Bagh","Prem Nagar",         27.563113, 80.669788, "VERIFIED"),
    ("MRU-5","Lohar Bagh","Sanjay Nagar",       27.559508, 80.678829, "VERIFIED"),

    # ── MRU-6 | Roti Godam ──
    ("MRU-6","Roti Godam","Shivpuri",           27.551579, 80.694123, "HIGH_SPREAD"),
    ("MRU-6","Roti Godam","Awas Vikas Block B", 27.557036, 80.694145, "VERIFIED"),
    ("MRU-6","Roti Godam","Brampuri",           27.555267, 80.673801, "VERIFIED"),
    ("MRU-6","Roti Godam","Gangdhar Nagar",     27.568016, 80.678952, "VERIFIED"),
    ("MRU-6","Roti Godam","Lal Kurti",          27.543446, 80.677859, "VERIFIED"),
    ("MRU-6","Roti Godam","Roti Godam",         27.557300, 80.670058, "VERIFIED"),
    ("MRU-6","Roti Godam","Sudamapuri",         27.556831, 80.672347, "HIGH_SPREAD"),
    ("MRU-6","Roti Godam","Sultanpur",          27.557300, 80.670058, "HIGH_SPREAD"),

    # ── MRU-7 | Husain Ganj ──
    ("MRU-7","Husain Ganj","Azad Nagar",        27.564767, 80.694089, "VERIFIED"),
    ("MRU-7","Husain Ganj","Budh Nagar",        27.547775, 80.709661, "HIGH_SPREAD"),
    ("MRU-7","Husain Ganj","Bijwal Khud",       27.531405, 80.715110, "HIGH_SPREAD"),
    ("MRU-7","Husain Ganj","Ginni Devi",        27.543827, 80.714863, "VERIFIED"),
    ("MRU-7","Husain Ganj","Sultanpur",         27.542446, 80.712929, "HIGH_SPREAD"),
    ("MRU-7","Husain Ganj","Jangal Kuti",       27.560290, 80.680703, "HIGH_SPREAD"),
]

MRU_COLORS = {
    "MRU-1": "#FF5252",
    "MRU-2": "#FF9800",
    "MRU-5": "#00BCD4",
    "MRU-6": "#2196F3",
    "MRU-7": "#9C27B0",
}

# ─── CIRCLE FALLBACK ───
def make_circle(lat, lon, radius_m=380, pts=36):
    ring = []
    for i in range(pts):
        a = math.radians(360 * i / pts)
        ring.append([
            lat + (radius_m / 111320) * math.cos(a),
            lon + (radius_m / (111320 * math.cos(math.radians(lat)))) * math.sin(a)
        ])
    ring.append(ring[0])
    return ring

# ─── OSM POLYGON FETCH ───
def fetch_polygon(sub, main, lat, lon):
    hdrs = {"User-Agent": "SitapurMapAgent/1.0"}
    for q in [f"{sub}, Sitapur, Uttar Pradesh, India",
               f"{sub}, {main}, Sitapur",
               f"{sub} Sitapur UP"]:
        try:
            res = requests.get("https://nominatim.openstreetmap.org/search",
                params={"q":q,"format":"json","limit":5,"polygon_geojson":1,
                        "countrycodes":"in","viewbox":"80.55,27.70,80.85,27.45","bounded":1},
                headers=hdrs, timeout=12).json()
            time.sleep(1.1)
            for item in res:
                if abs(float(item["lat"])-lat)>0.06 or abs(float(item["lon"])-lon)>0.06:
                    continue
                geo, gtype = item.get("geojson",{}), item.get("geojson",{}).get("type","")
                coords = geo.get("coordinates",[])
                if gtype == "Polygon" and coords:
                    ring = [[c[1],c[0]] for c in coords[0]]
                    print(f"  ✅ polygon  → {sub} ({len(ring)} pts)")
                    return ring, "polygon"
                if gtype == "MultiPolygon" and coords:
                    ring = [[c[1],c[0]] for c in max(coords,key=lambda p:len(p[0]))[0]]
                    print(f"  ✅ multipoly→ {sub} ({len(ring)} pts)")
                    return ring, "polygon"
                if gtype == "Point":
                    print(f"  📍 point    → {sub} (circle)")
                    return None, "point"
        except Exception as e:
            print(f"  ⚠️  {sub}: {e}"); time.sleep(2)
    print(f"  ❌ none     → {sub} (circle)")
    return None, "none"

# ─── HTML BUILDER ───
def build_html(data):
    js = "[\n" + ",\n".join([
        f'{{mru:{json.dumps(d["mru"])},main:{json.dumps(d["main"])},sub:{json.dumps(d["sub"])},'
        f'lat:{d["lat"]},lon:{d["lon"]},color:{json.dumps(d["color"])},'
        f'status:{json.dumps(d["status"])},shape:{json.dumps(d["shape"])},poly:{json.dumps(d["poly"])}}}'
        for d in data]) + "\n]"

    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sitapur PNG — Area Map</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',sans-serif;display:flex;height:100vh;overflow:hidden;background:#0d1117}
#sb{width:285px;min-width:285px;background:#0d1117;color:#e6e6e6;display:flex;flex-direction:column;border-right:1px solid #30363d}
#sh{padding:13px 15px;background:#161b22;border-bottom:1px solid #30363d}
#sh h2{font-size:14px;font-weight:700;color:#58a6ff}
#sh p{font-size:11px;color:#8b949e;margin-top:2px}
#ct{padding:8px 11px;background:#161b22;border-bottom:1px solid #30363d;display:flex;gap:5px;flex-wrap:wrap}
.cb{padding:4px 8px;border:1px solid #30363d;background:#21262d;color:#c9d1d9;border-radius:5px;cursor:pointer;font-size:11px;font-weight:500}
.cb:hover{background:#30363d}.cb.on{background:#1f6feb;border-color:#58a6ff;color:#fff}
#ml{flex:1;overflow-y:auto;padding:6px}
.ms{margin-bottom:5px}
.mh{padding:7px 10px;border-radius:5px;cursor:pointer;display:flex;align-items:center;gap:7px;font-size:12px;font-weight:600;border:1px solid #30363d;background:#161b22;user-select:none}
.md{width:10px;height:10px;border-radius:50%;flex-shrink:0}
.mc{margin-left:auto;font-size:10px;padding:1px 7px;border-radius:10px;background:#1a4731;color:#3fb950}
.sl{padding:3px 0 3px 15px;display:none}
.si{padding:5px 8px;margin:2px 0;border-radius:4px;cursor:pointer;font-size:11px;color:#8b949e;border-left:2px solid transparent;display:flex;justify-content:space-between;align-items:center}
.si:hover{color:#e6e6e6;background:#21262d}.si.on{color:#58a6ff;border-left-color:#58a6ff;background:#21262d}
.ss{font-size:9px;color:#484f58}
#ip{padding:11px 14px;background:#161b22;border-top:1px solid #30363d;min-height:90px}
#it{font-size:13px;font-weight:700;color:#e6e6e6;margin-bottom:3px}
#ib{font-size:11px;color:#8b949e;line-height:1.75}
#map{flex:1}
.leaflet-popup-content-wrapper{background:#161b22;color:#e6e6e6;border:1px solid #30363d;border-radius:8px}
.leaflet-popup-tip{background:#161b22}
.leaflet-popup-content{margin:11px 13px}
::-webkit-scrollbar{width:5px}::-webkit-scrollbar-track{background:#0d1117}::-webkit-scrollbar-thumb{background:#30363d;border-radius:3px}
</style>
</head>
<body>
<div id="sb">
  <div id="sh"><h2>🛰️ Sitapur PNG Areas</h2><p id="stat"></p></div>
  <div id="ct">
    <button class="cb on" onclick="fAll(this)">All</button>
    <button class="cb" onclick="fMRU(this,'MRU-1')">MRU-1</button>
    <button class="cb" onclick="fMRU(this,'MRU-2')">MRU-2</button>
    <button class="cb" onclick="fMRU(this,'MRU-5')">MRU-5</button>
    <button class="cb" onclick="fMRU(this,'MRU-6')">MRU-6</button>
    <button class="cb" onclick="fMRU(this,'MRU-7')">MRU-7</button>
    <button class="cb" onclick="map.setView([27.565,80.685],14)">⟳</button>
  </div>
  <div id="ml"></div>
  <div id="ip"><div id="it">← Click any area</div><div id="ib">Select from map or sidebar.</div></div>
</div>
<div id="map"></div>
<script>
const DATA=""" + js + """;

const map=L.map('map').setView([27.565,80.685],14);
const sat=L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
  {attribution:'Esri World Imagery',maxZoom:19}).addTo(map);
const lbl=L.tileLayer('https://{s}.basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}{r}.png',
  {attribution:'CartoDB',maxZoom:19,opacity:0.85,pane:'shadowPane'}).addTo(map);
L.control.layers({'🛰 Satellite':sat,'🗺 Street':L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19})},{}).addTo(map);

let LY={},ACT=null;

DATA.forEach((d,i)=>{
  const poly=L.polygon(d.poly,{
    color:d.color,weight:d.shape==='polygon'?2.2:1.8,opacity:0.9,
    fillColor:d.color,fillOpacity:0.2,dashArray:d.shape==='polygon'?null:'5,4'
  }).addTo(map);

  const lbl2=L.marker([d.lat,d.lon],{icon:L.divIcon({className:'',
    html:`<div style="background:${d.color}e0;color:#fff;padding:2px 6px;border-radius:3px;font-size:9px;font-weight:700;white-space:nowrap;box-shadow:0 1px 4px #0009;pointer-events:none">${d.sub}</div>`,
    iconAnchor:[0,8]}),zIndexOffset:-100}).addTo(map);

  poly.bindPopup(`<div style="min-width:175px">
    <b style="font-size:13px">${d.sub}</b><br>
    <span style="color:#8b949e;font-size:11px">${d.mru} · ${d.main}</span><br>
    <span style="color:#3fb950;font-size:11px;font-weight:600">✅ Charged</span><br>
    <span style="color:#484f58;font-size:10px">${d.lat.toFixed(5)}, ${d.lon.toFixed(5)}<br>${d.status} · ${d.shape}</span>
  </div>`);
  poly.on('click',()=>sel(i));
  LY[i]={poly,lbl:lbl2,d};
});

function sel(i){
  if(ACT!==null&&LY[ACT]){
    LY[ACT].poly.setStyle({weight:LY[ACT].d.shape==='polygon'?2.2:1.8,fillOpacity:0.2});
    const p=document.getElementById('si-'+ACT);if(p)p.classList.remove('on');
  }
  ACT=i;
  LY[i].poly.setStyle({weight:4,fillOpacity:0.45});
  map.flyTo([DATA[i].lat,DATA[i].lon],17,{duration:0.9});
  LY[i].poly.openPopup();
  const si=document.getElementById('si-'+i);
  if(si){si.classList.add('on');
    document.getElementById('sl-'+DATA[i].mru).style.display='block';
    si.scrollIntoView({behavior:'smooth',block:'nearest'});}
  const d=DATA[i];
  document.getElementById('it').textContent=d.sub;
  document.getElementById('ib').innerHTML=
    `<b>MRU:</b> ${d.mru}<br><b>Main:</b> ${d.main}<br>`+
    `<b>Status:</b> <span style="color:#3fb950">✅ Charged</span><br>`+
    `<b>Coords:</b> ${d.lat.toFixed(5)}, ${d.lon.toFixed(5)}<br>`+
    `<b>Shape:</b> ${d.shape} &nbsp;·&nbsp; <b>Source:</b> ${d.status}`;
}

function buildSB(){
  const g={};DATA.forEach((d,i)=>{(g[d.mru]=g[d.mru]||[]).push({...d,i});});
  const c=document.getElementById('ml');c.innerHTML='';
  Object.keys(g).sort().forEach(mru=>{
    const items=g[mru],sec=document.createElement('div');sec.className='ms';
    const hdr=document.createElement('div');hdr.className='mh';
    hdr.innerHTML=`<div class="md" style="background:${items[0].color}"></div>
      <span>${mru}</span>
      <span style="color:#8b949e;font-weight:400;font-size:10px">${items[0].main}</span>
      <span class="mc">${items.length}</span>`;
    const sl=document.createElement('div');sl.className='sl';sl.id='sl-'+mru;
    items.forEach(d=>{
      const it=document.createElement('div');it.className='si';it.id='si-'+d.i;
      it.innerHTML=`<span>${d.sub}</span><span class="ss">${d.shape==='polygon'?'⬡':'○'}</span>`;
      it.onclick=()=>sel(d.i);sl.appendChild(it);
    });
    hdr.onclick=()=>{const s=document.getElementById('sl-'+mru);s.style.display=s.style.display==='block'?'none':'block';};
    sec.appendChild(hdr);sec.appendChild(sl);c.appendChild(sec);
  });
  document.getElementById('stat').textContent=`${DATA.length} areas · 5 MRUs · All Charged`;
}

function fAll(btn){document.querySelectorAll('.cb').forEach(b=>b.classList.remove('on'));btn.classList.add('on');
  DATA.forEach((_,i)=>{map.addLayer(LY[i].poly);map.addLayer(LY[i].lbl);});}
function fMRU(btn,mru){document.querySelectorAll('.cb').forEach(b=>b.classList.remove('on'));btn.classList.add('on');
  DATA.forEach((d,i)=>{if(d.mru===mru){map.addLayer(LY[i].poly);map.addLayer(LY[i].lbl);}
    else{map.removeLayer(LY[i].poly);map.removeLayer(LY[i].lbl);}});
  const f=DATA.findIndex(d=>d.mru===mru);if(f>=0)map.flyTo([DATA[f].lat,DATA[f].lon],15,{duration:1});}

buildSB();
</script>
</body>
</html>"""
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

# ─── MAIN ───
def run(fetch_polygons=True):
    print(f"🚀 Sitapur Mapping Agent | {len(AREAS)} areas | fetch={fetch_polygons}\n")
    out = []
    for idx,(mru,main,sub,lat,lon,status) in enumerate(AREAS):
        print(f"[{idx+1:02}/{len(AREAS)}] {mru} | {sub}")
        poly, shape = (fetch_polygon(sub,main,lat,lon) if fetch_polygons else (None,"circle"))
        if poly is None:
            poly, shape = make_circle(lat,lon,380), "circle"
        out.append({"mru":mru,"main":main,"sub":sub,"lat":lat,"lon":lon,
                    "color":MRU_COLORS.get(mru,"#888"),"status":status,"shape":shape,"poly":poly})
    build_html(out)
    print(f"\n✅ Saved → {OUTPUT_HTML}")
    webbrowser.open(pathlib.Path(OUTPUT_HTML).resolve().as_uri())

if __name__ == "__main__":
    run(fetch_polygons="--no-fetch" not in sys.argv)
