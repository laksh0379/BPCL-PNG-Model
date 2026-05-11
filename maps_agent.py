from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import time, re, csv, statistics

# ─── SITAPUR DISTRICT BOUNDS (tight) ───
LAT_MIN, LAT_MAX = 27.45, 27.70
LON_MIN, LON_MAX = 80.55, 80.85

# ─── ALL 65 SUB-AREAS UNDER 8 MRUs ───
subareas = [
    # MRU-1 Naipalapur
    ("Adarsh Nagar",        "Naipalapur",   "MRU-1"),
    ("Anand Nagar",         "Naipalapur",   "MRU-1"),
    ("Bhawanpurva",         "Naipalapur",   "MRU-1"),
    ("Naipalapur",          "Naipalapur",   "MRU-1"),
    ("Prakash City",        "Naipalapur",   "MRU-1"),
    ("Rampurva",            "Naipalapur",   "MRU-1"),
    ("Rasoolganj",          "Naipalapur",   "MRU-1"),
    ("Sheeshmahal",         "Naipalapur",   "MRU-1"),
    # MRU-2 Panchampurva
    ("Ramakrishna Puri",    "Panchampurva", "MRU-2"),
    ("Panchampurva",        "Panchampurva", "MRU-2"),
    ("Guru Nanak Colony",   "Panchampurva", "MRU-2"),
    ("Gwal Mandi",          "Panchampurva", "MRU-2"),
    ("Subhash Nagar",       "Panchampurva", "MRU-2"),
    # MRU-3 Ghanta Ghar (UNCHARGED)
    ("Alam Nagar",          "Ghanta Ghar",  "MRU-3"),
    ("Buttas Ganj",         "Ghanta Ghar",  "MRU-3"),
    ("Dulhapurva",          "Ghanta Ghar",  "MRU-3"),
    ("Ghanta Ghar",         "Ghanta Ghar",  "MRU-3"),
    ("Godiyana",            "Ghanta Ghar",  "MRU-3"),
    ("Machi Mandi",         "Ghanta Ghar",  "MRU-3"),
    ("Nai Basti",           "Ghanta Ghar",  "MRU-3"),
    ("Pakka Bagh",          "Ghanta Ghar",  "MRU-3"),
    ("Patiya",              "Ghanta Ghar",  "MRU-3"),
    ("Ranikath",            "Ghanta Ghar",  "MRU-3"),
    ("Tareenpur",           "Ghanta Ghar",  "MRU-3"),
    ("Thekrapurva",         "Ghanta Ghar",  "MRU-3"),
    # MRU-4 Munshi Ganj (UNCHARGED)
    ("Ambedkar Nagar",      "Munshi Ganj",  "MRU-4"),
    ("Ambika Puram",        "Munshi Ganj",  "MRU-4"),
    ("Awadhpuri Colony",    "Munshi Ganj",  "MRU-4"),
    ("Begum Bagh",          "Munshi Ganj",  "MRU-4"),
    ("Hempurva",            "Munshi Ganj",  "MRU-4"),
    ("Holi Nagar",          "Munshi Ganj",  "MRU-4"),
    ("Munshi Ganj",         "Munshi Ganj",  "MRU-4"),
    ("Pusnagiri Nagar",     "Munshi Ganj",  "MRU-4"),
    # MRU-5 Lohar Bagh
    ("Agha Colony",         "Lohar Bagh",   "MRU-5"),
    ("Arya Nagar",          "Lohar Bagh",   "MRU-5"),
    ("Awas Vikas Block A",  "Lohar Bagh",   "MRU-5"),
    ("Awas Vikas Block C",  "Lohar Bagh",   "MRU-5"),
    ("Baijnath Colony",     "Lohar Bagh",   "MRU-5"),
    ("Chitra Colony",       "Lohar Bagh",   "MRU-5"),
    ("Civil Lines",         "Lohar Bagh",   "MRU-5"),
    ("Ghuramau Bangla",     "Lohar Bagh",   "MRU-5"),
    ("Kathalibagh",         "Lohar Bagh",   "MRU-5"),
    ("Lohar Bagh",          "Lohar Bagh",   "MRU-5"),
    ("Prem Nagar",          "Lohar Bagh",   "MRU-5"),
    ("Sanjay Nagar",        "Lohar Bagh",   "MRU-5"),
    # MRU-6 Roti Godam
    ("Shivpuri",            "Roti Godam",   "MRU-6"),
    ("Awas Vikas Block B",  "Roti Godam",   "MRU-6"),
    ("Sudamapuri",          "Roti Godam",   "MRU-6"),
    ("Brampuri",            "Roti Godam",   "MRU-6"),
    ("Gangdhar Nagar",      "Roti Godam",   "MRU-6"),
    ("Lal Kurti",           "Roti Godam",   "MRU-6"),
    ("Roti Godam",          "Roti Godam",   "MRU-6"),
    ("Sultanpur",           "Roti Godam",   "MRU-6"),
    # MRU-7 Husain Ganj
    ("Azad Nagar",          "Husain Ganj",  "MRU-7"),
    ("Budh Nagar",          "Husain Ganj",  "MRU-7"),
    ("Bijwal Khud",         "Husain Ganj",  "MRU-7"),
    ("Ginni Devi",          "Husain Ganj",  "MRU-7"),
    ("Husain Ganj",         "Husain Ganj",  "MRU-7"),
    ("Sultanpur",           "Husain Ganj",  "MRU-7"),
    ("Sadar Bazar",         "Husain Ganj",  "MRU-7"),
    ("Jangal Kuti",         "Husain Ganj",  "MRU-7"),
    # MRU-8 Khopur (UNCHARGED)
    ("Ahat Kaptan",         "Khopur",       "MRU-8"),
    ("Habipur Ahat",        "Khopur",       "MRU-8"),
    ("Bijanwa",             "Khopur",       "MRU-8"),
    ("Gaushala Purva",      "Khopur",       "MRU-8"),
    ("Habibpur",            "Khopur",       "MRU-8"),
]

# ─── SEARCH QUERY VARIANTS (tried in order if previous fails bounds check) ───
def build_queries(subarea, main_area):
    return [
        f"{subarea},{main_area},Sitapur,Uttar Pradesh",
        f"{subarea},Sitapur City,Uttar Pradesh",
        f"{subarea},Sitapur,UP,India",
        f"{subarea} near {main_area} Sitapur",
    ]

def in_bounds(lat, lon):
    return LAT_MIN < lat < LAT_MAX and LON_MIN < lon < LON_MAX

def get_coords(driver, query):
    """Load query, poll URL for @lat,lon up to 10s"""
    url = f"https://www.google.com/maps/search/{query.replace(' ', '+').replace(',', '%2C')}"
    driver.get(url)
    for _ in range(20):
        time.sleep(0.5)
        m = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', driver.current_url)
        if m:
            return float(m.group(1)), float(m.group(2))
    return None, None

def verify_coords(driver, subarea, main_area, lat, lon, attempts=5):
    """
    Re-fetch the same area N times and check consistency.
    Returns (verified_lat, verified_lon, spread) or None if inconsistent.
    """
    lats, lons = [lat], [lon]
    queries = build_queries(subarea, main_area)
    for i in range(attempts - 1):
        q = queries[i % len(queries)]
        la, lo = get_coords(driver, q)
        if la and in_bounds(la, lo):
            lats.append(la)
            lons.append(lo)
        time.sleep(0.3)

    if len(lats) < 3:
        return None, None, 999  # not enough consistent results

    spread_lat = max(lats) - min(lats)
    spread_lon = max(lons) - min(lons)
    max_spread = max(spread_lat, spread_lon)

    # Error margin < 0.1% of ~0.3 degree range ≈ 0.0003 degrees ≈ 30 meters
    if max_spread < 0.003:
        return statistics.median(lats), statistics.median(lons), max_spread
    else:
        return None, None, max_spread  # too inconsistent

# ─── DRIVER SETUP ───
options = webdriver.ChromeOptions()
options.binary_location = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(service=Service("/usr/local/bin/chromedriver"), options=options)
driver.set_page_load_timeout(15)

results = []
failed = []
print(f"🔍 Searching {len(subareas)} sub-areas with 5x verification...\n")

for subarea, main_area, mru in subareas:
    queries = build_queries(subarea, main_area)
    found_lat, found_lon = None, None

    # ── Step 1: Try each query variant until one lands in bounds ──
    for q in queries:
        lat, lon = get_coords(driver, q)
        if lat and in_bounds(lat, lon):
            found_lat, found_lon = lat, lon
            break
        elif lat:
            print(f"   ↳ Out of bounds ({lat:.4f},{lon:.4f}) trying next query...")

    if not found_lat:
        print(f"❌ {mru} | {subarea:25s} → ALL QUERIES FAILED")
        failed.append((mru, main_area, subarea))
        results.append([mru, main_area, subarea, None, None, "FAILED", 999])
        continue

    # ── Step 2: Verify 5 times for consistency ──
    v_lat, v_lon, spread = verify_coords(driver, subarea, main_area, found_lat, found_lon, attempts=5)

    if v_lat:
        print(f"✅ {mru} | {subarea:25s} → {v_lat:.5f}, {v_lon:.5f}  spread={spread:.5f}")
        results.append([mru, main_area, subarea, round(v_lat,6), round(v_lon,6), "VERIFIED", round(spread,6)])
    else:
        # Spread too high — use median of what we got but flag it
        print(f"⚠️  {mru} | {subarea:25s} → {found_lat:.5f}, {found_lon:.5f}  spread={spread:.5f} (HIGH)")
        results.append([mru, main_area, subarea, round(found_lat,6), round(found_lon,6), "HIGH_SPREAD", round(spread,6)])

driver.quit()

# ─── SAVE CSV ───
with open("sitapur_area_coordinates.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["MRU", "Main_Area", "Subarea", "Lat_Center", "Lon_Center", "Status", "Spread"])
    w.writerows(results)

verified  = sum(1 for r in results if r[5] == "VERIFIED")
high_sprd = sum(1 for r in results if r[5] == "HIGH_SPREAD")
failed_n  = sum(1 for r in results if r[5] == "FAILED")

print(f"\n{'='*60}")
print(f"✅ VERIFIED  : {verified}")
print(f"⚠️  HIGH SPREAD: {high_sprd}")
print(f"❌ FAILED    : {failed_n}")
print(f"💾 Saved → sitapur_area_coordinates.csv")
if failed:
    print(f"\nFailed areas to manually pin:")
    for f in failed:
        print(f"  {f[0]} | {f[2]} ({f[1]})")
