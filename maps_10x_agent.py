from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import time, re, csv, statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# ─── BOUNDS ───
LAT_MIN, LAT_MAX = 27.45, 27.70
LON_MIN, LON_MAX = 80.55, 80.85
ACCEPT_SPREAD    = 0.015
WORKERS          = 10  # parallel windows

subareas = [
    ("Adarsh Nagar",       "Naipalapur",   "MRU-1"),
    ("Anand Nagar",        "Naipalapur",   "MRU-1"),
    ("Bhawanpurva",        "Naipalapur",   "MRU-1"),
    ("Naipalapur",         "Naipalapur",   "MRU-1"),
    ("Prakash City",       "Naipalapur",   "MRU-1"),
    ("Rampurva",           "Naipalapur",   "MRU-1"),
    ("Rasoolganj",         "Naipalapur",   "MRU-1"),
    ("Sheeshmahal",        "Naipalapur",   "MRU-1"),
    ("Ramakrishna Puri",   "Panchampurva", "MRU-2"),
    ("Panchampurva",       "Panchampurva", "MRU-2"),
    ("Guru Nanak Colony",  "Panchampurva", "MRU-2"),
    ("Gwal Mandi",         "Panchampurva", "MRU-2"),
    ("Subhash Nagar",      "Panchampurva", "MRU-2"),
    ("Alam Nagar",         "Ghanta Ghar",  "MRU-3"),
    ("Buttas Ganj",        "Ghanta Ghar",  "MRU-3"),
    ("Dulhapurva",         "Ghanta Ghar",  "MRU-3"),
    ("Ghanta Ghar",        "Ghanta Ghar",  "MRU-3"),
    ("Godiyana",           "Ghanta Ghar",  "MRU-3"),
    ("Machi Mandi",        "Ghanta Ghar",  "MRU-3"),
    ("Nai Basti",          "Ghanta Ghar",  "MRU-3"),
    ("Pakka Bagh",         "Ghanta Ghar",  "MRU-3"),
    ("Patiya",             "Ghanta Ghar",  "MRU-3"),
    ("Ranikath",           "Ghanta Ghar",  "MRU-3"),
    ("Tareenpur",          "Ghanta Ghar",  "MRU-3"),
    ("Thekrapurva",        "Ghanta Ghar",  "MRU-3"),
    ("Ambedkar Nagar",     "Munshi Ganj",  "MRU-4"),
    ("Ambika Puram",       "Munshi Ganj",  "MRU-4"),
    ("Awadhpuri Colony",   "Munshi Ganj",  "MRU-4"),
    ("Begum Bagh",         "Munshi Ganj",  "MRU-4"),
    ("Hempurva",           "Munshi Ganj",  "MRU-4"),
    ("Holi Nagar",         "Munshi Ganj",  "MRU-4"),
    ("Munshi Ganj",        "Munshi Ganj",  "MRU-4"),
    ("Pusnagiri Nagar",    "Munshi Ganj",  "MRU-4"),
    ("Agha Colony",        "Lohar Bagh",   "MRU-5"),
    ("Arya Nagar",         "Lohar Bagh",   "MRU-5"),
    ("Awas Vikas Block A", "Lohar Bagh",   "MRU-5"),
    ("Awas Vikas Block C", "Lohar Bagh",   "MRU-5"),
    ("Baijnath Colony",    "Lohar Bagh",   "MRU-5"),
    ("Chitra Colony",      "Lohar Bagh",   "MRU-5"),
    ("Civil Lines",        "Lohar Bagh",   "MRU-5"),
    ("Ghuramau Bangla",    "Lohar Bagh",   "MRU-5"),
    ("Kathalibagh",        "Lohar Bagh",   "MRU-5"),
    ("Lohar Bagh",         "Lohar Bagh",   "MRU-5"),
    ("Prem Nagar",         "Lohar Bagh",   "MRU-5"),
    ("Sanjay Nagar",       "Lohar Bagh",   "MRU-5"),
    ("Shivpuri",           "Roti Godam",   "MRU-6"),
    ("Awas Vikas Block B", "Roti Godam",   "MRU-6"),
    ("Sudamapuri",         "Roti Godam",   "MRU-6"),
    ("Brampuri",           "Roti Godam",   "MRU-6"),
    ("Gangdhar Nagar",     "Roti Godam",   "MRU-6"),
    ("Lal Kurti",          "Roti Godam",   "MRU-6"),
    ("Roti Godam",         "Roti Godam",   "MRU-6"),
    ("Sultanpur",          "Roti Godam",   "MRU-6"),
    ("Azad Nagar",         "Husain Ganj",  "MRU-7"),
    ("Budh Nagar",         "Husain Ganj",  "MRU-7"),
    ("Bijwal Khud",        "Husain Ganj",  "MRU-7"),
    ("Ginni Devi",         "Husain Ganj",  "MRU-7"),
    ("Husain Ganj",        "Husain Ganj",  "MRU-7"),
    ("Sultanpur",          "Husain Ganj",  "MRU-7"),
    ("Sadar Bazar",        "Husain Ganj",  "MRU-7"),
    ("Jangal Kuti",        "Husain Ganj",  "MRU-7"),
    ("Ahat Kaptan",        "Khopur",       "MRU-8"),
    ("Habipur Ahat",       "Khopur",       "MRU-8"),
    ("Bijanwa",            "Khopur",       "MRU-8"),
    ("Gaushala Purva",     "Khopur",       "MRU-8"),
    ("Habibpur",           "Khopur",       "MRU-8"),
]

print_lock = threading.Lock()
def log(msg):
    with print_lock:
        print(msg, flush=True)

def make_driver():
    options = webdriver.ChromeOptions()
    options.binary_location = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--headless=new")   # ← no visible windows, much faster
    options.add_argument("--window-size=1280,800")
    d = webdriver.Chrome(service=Service("/usr/local/bin/chromedriver"), options=options)
    d.set_page_load_timeout(12)
    return d

def build_queries(subarea, main_area):
    return [
        f"{subarea},{main_area},Sitapur,Uttar Pradesh",
        f"{subarea},Sitapur City,Uttar Pradesh",
        f"{subarea},Sitapur,UP,India",
        f"{subarea} near {main_area} Sitapur",
        f"{subarea} Sitapur",
    ]

def in_bounds(lat, lon):
    return LAT_MIN < lat < LAT_MAX and LON_MIN < lon < LON_MAX

def get_coords(driver, query):
    url = f"https://www.google.com/maps/search/{query.replace(' ', '+').replace(',', '%2C')}"
    try:
        driver.get(url)
    except Exception:
        return None, None
    for _ in range(20):
        time.sleep(0.4)
        m = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', driver.current_url)
        if m:
            return float(m.group(1)), float(m.group(2))
    return None, None

def fetch_n(driver, subarea, main_area, n):
    queries = build_queries(subarea, main_area)
    lats, lons = [], []
    for i in range(n):
        la, lo = get_coords(driver, queries[i % len(queries)])
        if la and in_bounds(la, lo):
            lats.append(la)
            lons.append(lo)
        time.sleep(0.1)
    return lats, lons

def assess(lats, lons):
    if len(lats) < 3:
        return None, None, 999.0
    spread = max(max(lats) - min(lats), max(lons) - min(lons))
    return statistics.median(lats), statistics.median(lons), spread

def process_one(item):
    subarea, main_area, mru = item
    driver = make_driver()
    try:
        # Pass 1: 5x
        lats, lons = fetch_n(driver, subarea, main_area, n=5)
        lat, lon, spread = assess(lats, lons)

        if lat and spread <= ACCEPT_SPREAD:
            log(f"✅ {mru} | {subarea:25s} → {lat:.5f},{lon:.5f}  spread={spread:.5f}")
            return [mru, main_area, subarea, round(lat,6), round(lon,6), "VERIFIED", round(spread,6)]

        # Pass 2: 10x
        log(f"🔄 {mru} | {subarea:25s} → retrying 10x (spread={spread:.5f})...")
        lats2, lons2 = fetch_n(driver, subarea, main_area, n=10)
        lat2, lon2, spread2 = assess(lats2, lons2)

        if lat2 and spread2 <= ACCEPT_SPREAD:
            log(f"   ✅ {mru} | {subarea:25s} → {lat2:.5f},{lon2:.5f}  spread={spread2:.5f} (10x)")
            return [mru, main_area, subarea, round(lat2,6), round(lon2,6), "VERIFIED_10X", round(spread2,6)]
        elif lat2:
            log(f"   ⚠️  {mru} | {subarea:25s} → {lat2:.5f},{lon2:.5f}  spread={spread2:.5f} HIGH")
            return [mru, main_area, subarea, round(lat2,6), round(lon2,6), "HIGH_SPREAD", round(spread2,6)]
        else:
            log(f"   ❌ {mru} | {subarea:25s} → FAILED")
            return [mru, main_area, subarea, None, None, "FAILED", 999]
    finally:
        driver.quit()

# ─── MAIN ───
print(f"🚀 {WORKERS} parallel workers | {len(subareas)} sub-areas\n")
start = time.time()

results_map = {}
with ThreadPoolExecutor(max_workers=WORKERS) as executor:
    futures = {executor.submit(process_one, item): item for item in subareas}
    for future in as_completed(futures):
        item = futures[future]
        try:
            results_map[item] = future.result()
        except Exception as e:
            log(f"💥 {item[0]} CRASHED: {e}")
            results_map[item] = [item[2], item[1], item[0], None, None, "CRASHED", 999]

results = [results_map[item] for item in subareas]
elapsed = time.time() - start
print(f"\n⏱  Done in {elapsed:.0f}s ({elapsed/60:.1f} min)")

with open("sitapur_area_coordinates.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["MRU","Main_Area","Subarea","Lat_Center","Lon_Center","Status","Spread"])
    w.writerows(results)

v1   = sum(1 for r in results if r[5] == "VERIFIED")
v10  = sum(1 for r in results if r[5] == "VERIFIED_10X")
high = sum(1 for r in results if r[5] == "HIGH_SPREAD")
fail = sum(1 for r in results if r[5] in ("FAILED","CRASHED"))

print(f"\n{'='*55}")
print(f"✅ VERIFIED (5x)  : {v1}")
print(f"✅ VERIFIED (10x) : {v10}")
print(f"⚠️  HIGH SPREAD    : {high}")
print(f"❌ FAILED         : {fail}")
print(f"💾 → sitapur_area_coordinates.csv")

need_manual = [r for r in results if r[5] in ("FAILED","CRASHED","HIGH_SPREAD")]
if need_manual:
    print(f"\n📌 {len(need_manual)} need manual check:")
    for r in need_manual:
        coord = f"{r[3]:.5f},{r[4]:.5f}" if r[3] else "NO COORDS"
        print(f"  {r[0]} | {r[2]:25s} | {r[5]:12s} | {coord}")
