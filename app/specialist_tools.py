"""Specialist tools for TrailCraft multi-agent system.

Includes:
1. Pack, Nutrition & Water Calculator (Ultralight / No-Cook optimization)
2. Alpine Weather & Conditions Fetcher (Open-Meteo live mountain forecast)
3. Permit & Lottery Guidance Specialist (Washington quota zones & regulations)
"""

import json
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional
from app.firestore_tools import PROJECT_ID, list_gear_inventory, get_trail_details

GCS_BUCKET_NAME = "bwg3-qwiklabs-gcp-03-c022e089199f"
IMAGE_MODEL_NAME = "gemini-3.1-flash-lite-image"
IMAGE_LOCATION = "global"


def calculate_pack_nutrition_and_water(
    trail_id: str,
    custom_days: Optional[int] = None,
    water_capacity_liters: float = 2.0,
    daily_calorie_target: int = 3200,
) -> Dict[str, Any]:
    """Calculate total pack weight, no-cook nutrition requirements, and water carry strategy.

    Args:
        trail_id: ID of the trail in the catalog (e.g. 'enchantments-traverse', 'wonderland-trail-mt-rainier').
        custom_days: Optional override for trip duration in days.
        water_capacity_liters: Total water carrying capacity (default 2.0L).
        daily_calorie_target: Daily energy target in calories (default 3200 kcal for hard hikes).

    Returns:
        Breakdown of base weight, consumable food weight, water weight, and estimated hiking hours (Naismith's rule).
    """
    trail = get_trail_details(trail_id)
    if "error" in trail:
        return {"error": trail["error"]}

    distance_miles = trail.get("distance_miles", 10.0)
    elevation_gain_ft = trail.get("elevation_gain_ft", 2000)
    duration_days = custom_days or trail.get("duration_days", 2)
    water_sources = trail.get("water_sources", [])

    # Fetch gear from user's inventory
    gear_items = list_gear_inventory()
    base_weight_oz = sum(item.get("weight_oz", 0.0) for item in gear_items)
    base_weight_lbs = round(base_weight_oz / 16.0, 2)

    # Consumable Food Math for No-Cook strategy:
    # High-density no-cook foods average ~130 calories per ounce (nuts, seed butters, olive oil, dried meats).
    cal_per_oz = 130.0
    food_oz_per_day = daily_calorie_target / cal_per_oz
    total_food_oz = food_oz_per_day * duration_days
    total_food_lbs = round(total_food_oz / 16.0, 2)

    # Water Strategy:
    # 1 Liter of water weighs 35.2 oz (2.20 lbs).
    # If trail has plentiful water sources (> 3 named sources), recommend carrying 1.0 - 1.5L at a time.
    # Check if trail explicitly notes no reliable water or is empty
    is_dry = (
        len(water_sources) == 0
        or any("none" in str(s).lower() or "no reliable" in str(s).lower() for s in water_sources)
    )

    if is_dry:
        recommended_water_carry_liters = max(water_capacity_liters, 3.0)
        water_advice = (
            "Dry route or scarce water sources! Camel up at trailhead and carry at least 3.0L."
        )
    elif len(water_sources) >= 3:
        recommended_water_carry_liters = 1.25
        water_advice = (
            f"Trail has frequent water ({', '.join(water_sources[:3])}). "
            f"Carry only 1.25L between sources to save ~1.6 lbs of carried water weight."
        )
    else:
        recommended_water_carry_liters = min(water_capacity_liters, 2.0)
        water_advice = (
            f"Moderate water availability ({', '.join(water_sources)}). "
            f"Carry {recommended_water_carry_liters}L and top off at every crossing."
        )

    water_weight_lbs = round(recommended_water_carry_liters * 2.20462, 2)
    total_trail_weight_lbs = round(base_weight_lbs + total_food_lbs + water_weight_lbs, 2)

    # Naismith's Rule with Trudge adjustment:
    # 3 mph flat + 1 hour per 2000 ft ascent
    estimated_hours = round((distance_miles / 2.7) + (elevation_gain_ft / 1800.0), 1)

    return {
        "trail_name": trail.get("name"),
        "trip_duration_days": duration_days,
        "base_pack_weight_lbs": base_weight_lbs,
        "food_plan": {
            "strategy": "No-Cook / Cold Soak Ultralight",
            "daily_calories": daily_calorie_target,
            "caloric_density": f"{cal_per_oz} cal/oz",
            "daily_food_weight_oz": round(food_oz_per_day, 1),
            "total_food_weight_lbs": total_food_lbs,
            "recommended_staples": [
                "Nut butter packets (macadamia/almond)",
                "Pemmican or beef biltong",
                "Freeze-dried meals (cold-soak in Talenti jar)",
                "Dried fruit & roasted salted seeds",
                "Electrolyte tablets"
            ]
        },
        "water_strategy": {
            "recommended_carry_liters": recommended_water_carry_liters,
            "recommended_carry_weight_lbs": water_weight_lbs,
            "water_sources_count": len(water_sources),
            "advice": water_advice
        },
        "total_starting_pack_weight_lbs": total_trail_weight_lbs,
        "estimated_total_hiking_hours": estimated_hours,
        "hours_per_day": round(estimated_hours / duration_days, 1)
    }


# Trail coordinate map for Washington alpine regions
TRAIL_COORDINATES = {
    "enchantments-traverse": {"lat": 47.534, "lon": -120.760, "name": "Leavenworth / Alpine Lakes"},
    "wonderland-trail-mt-rainier": {"lat": 46.852, "lon": -121.760, "name": "Mount Rainier"},
    "spider-gap-buck-creek-pass-loop": {"lat": 48.067, "lon": -120.840, "name": "Glacier Peak Wilderness"},
    "mount-olympus-hoh-river-trail": {"lat": 47.860, "lon": -123.934, "name": "Olympic Mountains / Hoh"},
    "ptarmigan-traverse": {"lat": 48.513, "lon": -121.058, "name": "North Cascades Cascade Pass"},
    "mailbox-peak-old-trail": {"lat": 47.467, "lon": -121.674, "name": "North Bend / Snoqualmie"},
    "mount-st-helens-monitor-ridge": {"lat": 46.191, "lon": -122.195, "name": "Mount St. Helens"},
    "gothic-basin": {"lat": 47.986, "lon": -121.464, "name": "Mountain Loop Highway"},
    "sahale-arm-cascade-pass": {"lat": 48.513, "lon": -121.058, "name": "Sahale Arm / Cascade Pass"},
    "colchuck-lake": {"lat": 47.534, "lon": -120.760, "name": "Stuart Range / Colchuck"}
}


def fetch_trail_weather_and_conditions(trail_id: str) -> Dict[str, Any]:
    """Fetch live alpine weather and conditions for a trail's location using Open-Meteo.

    Args:
        trail_id: The ID of the trail (e.g. 'enchantments-traverse', 'wonderland-trail-mt-rainier').

    Returns:
        Current temperature, wind speed, weather conditions, and safety notices for alpine terrain.
    """
    coords = TRAIL_COORDINATES.get(trail_id, {"lat": 47.5, "lon": -121.0, "name": "Washington Cascades"})
    lat = coords["lat"]
    lon = coords["lon"]
    loc_name = coords["name"]

    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,"
        f"apparent_temperature,precipitation,wind_speed_10m,wind_gusts_10m,weather_code"
        f"&temperature_unit=fahrenheit&wind_speed_unit=mph&precipitation_unit=inch"
    )

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TrailCraft-Agent/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            current = data.get("current", {})

            temp = current.get("temperature_2m")
            feels_like = current.get("apparent_temperature")
            humidity = current.get("relative_humidity_2m")
            wind_speed = current.get("wind_speed_10m")
            wind_gusts = current.get("wind_gusts_10m")
            precip = current.get("precipitation", 0.0)

            # Alpine safety advisory based on wind and temp
            advisory = "Favorable conditions."
            if temp is not None and temp < 40:
                advisory = "Cold alpine temps! Ensure insulating sleep layers (quilt + insulated pad) are packed."
            if wind_speed is not None and wind_speed > 25:
                advisory = "High exposed ridge winds! Pitch tent low with solid stake anchors."
            if precip is not None and precip > 0.1:
                advisory = "Precipitation active. Wet rocks on scramble sections will be slick."

            return {
                "trail_id": trail_id,
                "region_name": loc_name,
                "coordinates": {"latitude": lat, "longitude": lon},
                "temperature_f": temp,
                "feels_like_f": feels_like,
                "humidity_percent": humidity,
                "wind_speed_mph": wind_speed,
                "wind_gusts_mph": wind_gusts,
                "precipitation_inches": precip,
                "alpine_advisory": advisory
            }
    except Exception as e:
        return {
            "error": f"Failed to retrieve weather for {trail_id}: {str(e)}",
            "fallback_info": f"Standard Cascade alpine conditions apply for {loc_name}."
        }


def get_permit_and_lottery_guidance(trail_id: str) -> Dict[str, Any]:
    """Retrieve comprehensive permit regulations, lottery dates, and direct links for Washington routes.

    Args:
        trail_id: The ID of the trail (e.g. 'enchantments-traverse', 'wonderland-trail-mt-rainier').

    Returns:
        Permit type, quota window, lottery procedure, and ranger contact/links.
    """
    trail = get_trail_details(trail_id)
    if "error" in trail:
        return {"error": trail["error"]}

    permits_required = trail.get("permits_required", False)
    permit_details = trail.get("permit_details", "No special permit required.")

    # Tailored guidance by zone
    if "enchantments" in trail_id:
        guidance = {
            "zone": "Enchantments Core / Colchuck / Snow Lakes",
            "lottery_window": "Annually February 15 - March 1 on Recreation.gov",
            "secondary_walk_up": "Unclaimed permits released on Recreation.gov each Sunday at 7 AM PT.",
            "day_use": "Free self-issued permit available at the Stuart/Colchuck trailhead kiosk (no quota for day thru-hikes).",
            "regulations": "Campfires strictly prohibited in Core. Solid human waste must go into backcountry toilets or blue bags. Bear canisters or wire bags recommended.",
            "permit_portal": "https://www.recreation.gov/permits/233273"
        }
    elif "wonderland" in trail_id:
        guidance = {
            "zone": "Mount Rainier National Park Backcountry",
            "lottery_window": "Early Access Lottery in February-March on Recreation.gov.",
            "walk_up": "Approximately 30% of backcountry permits held for in-person walk-ups (max 24-48 hours in advance at Longmire or White River Wilderness Information Centers).",
            "regulations": "Must camp in designated backcountry camps. Bear poles provided at camps (bear canister optional but good practice).",
            "permit_portal": "https://www.recreation.gov/permits/4675317"
        }
    elif "st-helens" in trail_id:
        guidance = {
            "zone": "Mount St. Helens National Volcanic Monument",
            "lottery_window": "Monthly release on Recreation.gov on the first day of preceding month (e.g. May permits release April 1).",
            "regulations": "Climbing permit mandatory above 4,800 ft. No camping in the crater or on the rim.",
            "permit_portal": "https://www.recreation.gov/permits/4675311"
        }
    elif "olympus" in trail_id or "constance" in trail_id:
        guidance = {
            "zone": "Olympic National Park Wilderness",
            "lottery_window": "Reservations open April 15 on Recreation.gov.",
            "regulations": "Bear canisters mandatory in Hoh River, Sol Duc, and high subalpine zones. Hang wires exist only in select lower camps.",
            "permit_portal": "https://www.recreation.gov/permits/4098362"
        }
    else:
        guidance = {
            "zone": trail.get("region", "USFS Wilderness, WA"),
            "lottery_window": "No advance lottery required.",
            "day_and_overnight": "Free self-issued wilderness permit at the trailhead kiosk.",
            "parking_pass": "Northwest Forest Pass or America the Beautiful Interagency Pass required at trailhead.",
            "regulations": "Leave No Trace principles; camp at least 100-200 ft from lakes and streams."
        }

    return {
        "trail_id": trail_id,
        "trail_name": trail.get("name"),
        "permits_required": permits_required,
        "overview": permit_details,
        "detailed_guidance": guidance
    }


def get_trail_daylight_and_sun_times(trail_id: str, date_str: Optional[str] = None) -> Dict[str, Any]:
    """Fetch sunrise, sunset, first light, and daylight duration from the Sunrise-Sunset public API.

    Crucial for alpine hikers to calculate usable daylight hours, headlamp start times,
    and avoid getting stranded after dusk on technical scramble terrain.

    Args:
        trail_id: The ID of the trail (e.g. 'enchantments-traverse', 'wonderland-trail-mt-rainier').
        date_str: Optional date in 'YYYY-MM-DD' format (defaults to current date).

    Returns:
        Sunrise, sunset, civil twilight times (first/last light in Pacific Time), and total daylight duration.
    """
    coords = TRAIL_COORDINATES.get(trail_id, {"lat": 47.5, "lon": -121.0, "name": "Washington Cascades"})
    lat = coords["lat"]
    lon = coords["lon"]

    url = f"https://api.sunrise-sunset.org/json?lat={lat}&lng={lon}&formatted=0"
    if date_str:
        url += f"&date={date_str}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TrailCraft-Agent/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
            if payload.get("status") != "OK":
                return {"error": "Failed to get daylight info from Sunrise-Sunset API."}

            res = payload.get("results", {})

            # Convert UTC times to local Pacific Time (America/Los_Angeles)
            from datetime import datetime
            from zoneinfo import ZoneInfo
            pac_tz = ZoneInfo("America/Los_Angeles")

            def to_pacific(iso_str: str) -> str:
                dt_utc = datetime.fromisoformat(iso_str)
                dt_pac = dt_utc.astimezone(pac_tz)
                return dt_pac.strftime("%I:%M %p %Z")

            sunrise_pac = to_pacific(res["sunrise"])
            sunset_pac = to_pacific(res["sunset"])
            first_light_pac = to_pacific(res["civil_twilight_begin"])
            last_light_pac = to_pacific(res["civil_twilight_end"])

            day_length_sec = res.get("day_length", 0)
            day_hours = round(day_length_sec / 3600.0, 1)

            return {
                "trail_id": trail_id,
                "location_name": coords.get("name"),
                "date": date_str or "today",
                "first_usable_light": first_light_pac,
                "sunrise": sunrise_pac,
                "sunset": sunset_pac,
                "last_usable_light": last_light_pac,
                "total_daylight_hours": day_hours,
                "tactical_guidance": (
                    f"Plan to clear exposed alpine passes and establish camp before last light ({last_light_pac}). "
                    f"Alpine start under headlamp can safely transition to natural light at {first_light_pac}."
                )
            }
    except Exception as e:
        return {"error": f"Daylight API error for {trail_id}: {str(e)}"}


# ==============================================================================
# OFFLINE MAPS & NAVIGATION TOOL
# ==============================================================================

TRAIL_MAP_DATA = {
    "enchantments-traverse": {
        "trailhead_name": "Stuart / Colchuck Lake Trailhead",
        "trailhead_lat": 47.534,
        "trailhead_lon": -120.760,
        "exit_trailhead": "Snow Lakes Trailhead (point-to-point shuttle required)",
        "caltopo_map_url": "https://caltopo.com/map.html#ll=47.502,-120.789&z=13&b=topo",
        "gpx_download_url": "https://caltopo.com/m/8K4N",
        "offline_app_links": {
            "gaia_gps": "https://www.gaiagps.com/hike/united-states/washington/alpine-lakes-wilderness/the-enchantments-thru-hike/",
            "alltrails": "https://www.alltrails.com/trail/us/washington/the-enchantments-trail",
            "google_maps_directions": "https://www.google.com/maps/dir/?api=1&destination=47.534,-120.760"
        }
    },
    "wonderland-trail-mt-rainier": {
        "trailhead_name": "Longmire / White River Wilderness Center",
        "trailhead_lat": 46.750,
        "trailhead_lon": -121.812,
        "exit_trailhead": "Loop trail (returns to starting ranger station)",
        "caltopo_map_url": "https://caltopo.com/map.html#ll=46.852,-121.760&z=11&b=topo",
        "gpx_download_url": "https://caltopo.com/m/7P1M",
        "offline_app_links": {
            "gaia_gps": "https://www.gaiagps.com/hike/united-states/washington/mount-rainier-national-park/wonderland-trail/",
            "alltrails": "https://www.alltrails.com/trail/us/washington/wonderland-trail",
            "google_maps_directions": "https://www.google.com/maps/dir/?api=1&destination=46.750,-121.812"
        }
    },
    "spider-gap-buck-creek-pass-loop": {
        "trailhead_name": "Phelps Creek Trailhead",
        "trailhead_lat": 48.077,
        "trailhead_lon": -120.840,
        "exit_trailhead": "Trinity Trailhead (short road walk or key swap)",
        "caltopo_map_url": "https://caltopo.com/map.html#ll=48.125,-120.890&z=12&b=topo",
        "gpx_download_url": "https://caltopo.com/m/9D4K",
        "offline_app_links": {
            "gaia_gps": "https://www.gaiagps.com/hike/united-states/washington/glacier-peak-wilderness/spider-gap-buck-creek-pass-loop/",
            "alltrails": "https://www.alltrails.com/trail/us/washington/spider-gap-buck-creek-pass-loop",
            "google_maps_directions": "https://www.google.com/maps/dir/?api=1&destination=48.077,-120.840"
        }
    },
    "mount-olympus-hoh-river-trail": {
        "trailhead_name": "Hoh Rain Forest Visitor Center",
        "trailhead_lat": 47.860,
        "trailhead_lon": -123.934,
        "exit_trailhead": "Out-and-back from Hoh Visitor Center",
        "caltopo_map_url": "https://caltopo.com/map.html#ll=47.810,-123.750&z=12&b=topo",
        "gpx_download_url": "https://caltopo.com/m/4T6E",
        "offline_app_links": {
            "gaia_gps": "https://www.gaiagps.com/hike/united-states/washington/olympic-national-park/mount-olympus-via-hoh-river-trail/",
            "alltrails": "https://www.alltrails.com/trail/us/washington/hoh-river-trail-to-blue-glacier-moraine",
            "google_maps_directions": "https://www.google.com/maps/dir/?api=1&destination=47.860,-123.934"
        }
    }
}


def get_trailhead_navigation_and_offline_map(trail_id: str) -> Dict[str, Any]:
    """Retrieve Google Maps trailhead driving directions and offline topo GPX map links for GPS apps.

    Args:
        trail_id: The ID of the trail in the catalog (e.g. 'enchantments-traverse', 'wonderland-trail-mt-rainier').

    Returns:
        Google Maps navigation link, trailhead GPS coordinates, downloadable GPX track, and CalTopo/Gaia offline links.
    """
    trail = get_trail_details(trail_id)
    if "error" in trail:
        return {"error": trail["error"]}

    map_info = TRAIL_MAP_DATA.get(trail_id)
    if not map_info:
        coords = TRAIL_COORDINATES.get(trail_id, {"lat": 47.5, "lon": -121.0, "name": trail.get("region", "WA")})
        lat = coords["lat"]
        lon = coords["lon"]
        map_info = {
            "trailhead_name": f"{trail.get('name')} Trailhead",
            "trailhead_lat": lat,
            "trailhead_lon": lon,
            "exit_trailhead": "Same as entrance (check route profile)",
            "caltopo_map_url": f"https://caltopo.com/map.html#ll={lat},{lon}&z=13&b=topo",
            "gpx_download_url": trail.get("offline_map_url", "https://caltopo.com/"),
            "offline_app_links": {
                "gaia_gps": "https://www.gaiagps.com/",
                "alltrails": "https://www.alltrails.com/",
                "google_maps_directions": f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}"
            }
        }

    return {
        "trail_id": trail_id,
        "trail_name": trail.get("name"),
        "trailhead": {
            "name": map_info["trailhead_name"],
            "coordinates": f"{map_info['trailhead_lat']}, {map_info['trailhead_lon']}",
            "google_maps_driving_url": map_info["offline_app_links"]["google_maps_directions"],
            "exit_logistics": map_info["exit_trailhead"]
        },
        "offline_navigation": {
            "caltopo_interactive_topo": map_info["caltopo_map_url"],
            "gpx_direct_download": map_info["gpx_download_url"],
            "recommended_gps_apps": ["Gaia GPS", "CalTopo Mobile", "Garmin Explore / inReach"],
            "offline_procedure": (
                "Download the offline GPX track and topo map tiles onto your phone/inReach before leaving cell range. "
                "Washington trailheads in the Cascades and Olympics generally have zero cellular reception."
            )
        }
    }


# ==============================================================================
# SNACK CALORIES & PRICING TOOL
# ==============================================================================

ULTRALIGHT_SNACK_CATALOG = {
    "macadamia-nuts": {
        "name": "Raw or Dry Roasted Macadamia Nuts",
        "category": "Nuts & Seeds",
        "serving_size_oz": 1.0,
        "calories_per_oz": 204,
        "fat_g_per_oz": 21.5,
        "protein_g_per_oz": 2.2,
        "carbs_g_per_oz": 3.9,
        "typical_price_per_lb": 14.99,
        "price_per_1000_cal": 4.59,
        "ultralight_rating": "Elite (Highest calorie density in nature)",
        "notes": "King of ultralight backpacking foods. Extreme calorie density reduces pack bulk."
    },
    "peanut-butter-packets": {
        "name": "Justin's Classic Peanut Butter Squeeze Packs (1.15 oz)",
        "category": "Nut Butters",
        "serving_size_oz": 1.15,
        "calories_per_oz": 165,
        "fat_g_per_oz": 14.0,
        "protein_g_per_oz": 6.1,
        "carbs_g_per_oz": 5.2,
        "typical_price_per_lb": 8.50,
        "price_per_1000_cal": 3.20,
        "ultralight_rating": "Excellent",
        "notes": "Convenient no-mess squeeze pouch. Great on tortillas or eaten straight."
    },
    "beef-biltong-jerky": {
        "name": "Grass-Fed Beef Biltong / Jerky",
        "category": "Dried Meats",
        "serving_size_oz": 1.0,
        "calories_per_oz": 110,
        "fat_g_per_oz": 3.5,
        "protein_g_per_oz": 16.0,
        "carbs_g_per_oz": 1.0,
        "typical_price_per_lb": 18.00,
        "price_per_1000_cal": 10.20,
        "ultralight_rating": "High Protein Staple",
        "notes": "Biltong is air-dried without added sugar; higher protein and tender compared to traditional jerky."
    },
    "olive-oil-packets": {
        "name": "Extra Virgin Olive Oil Squeeze Packs",
        "category": "Fats & Oils",
        "serving_size_oz": 0.5,
        "calories_per_oz": 240,
        "fat_g_per_oz": 28.0,
        "protein_g_per_oz": 0.0,
        "carbs_g_per_oz": 0.0,
        "typical_price_per_lb": 12.00,
        "price_per_1000_cal": 3.12,
        "ultralight_rating": "God Tier Calorie Density",
        "notes": "Add 1-2 packets into cold-soak meals, ramen, or nut butter to instantly boost calories by 240 cal/oz."
    },
    "probar-meal": {
        "name": "PROBAR Meal Bar (Superfood Slam)",
        "category": "Meal Bars",
        "serving_size_oz": 3.0,
        "calories_per_oz": 133,
        "fat_g_per_oz": 5.7,
        "protein_g_per_oz": 3.3,
        "carbs_g_per_oz": 16.0,
        "typical_price_per_lb": 16.00,
        "price_per_1000_cal": 7.50,
        "ultralight_rating": "Great All-in-One",
        "notes": "400 calories per bar. Certified organic, vegan, dense whole-food ingredients."
    },
    "dried-mango-slices": {
        "name": "Unsweetened Dried Mango Slices",
        "category": "Dried Fruit",
        "serving_size_oz": 1.5,
        "calories_per_oz": 95,
        "fat_g_per_oz": 0.5,
        "protein_g_per_oz": 1.0,
        "carbs_g_per_oz": 22.0,
        "typical_price_per_lb": 9.99,
        "price_per_1000_cal": 6.55,
        "ultralight_rating": "Quick Energy Carbs",
        "notes": "Fast-acting glycogen replenisher on steep uphill mountain climbs."
    }
}


def lookup_ultralight_trail_snack(query: str = "") -> Dict[str, Any]:
    """Look up nutritional specs (calories, fat, protein, cal/oz) and pricing for backpacking snacks.

    Evaluates whether foods meet the ultralight standard of >= 125 calories/ounce.

    Args:
        query: Snack name or category to search (e.g. 'nuts', 'macadamia', 'jerky', 'peanut butter', 'probar', 'oil').

    Returns:
        List of matching snacks with caloric density, macro breakdown, typical pricing, and efficiency score.
    """
    q = query.lower().strip()
    results = []

    for item_id, item in ULTRALIGHT_SNACK_CATALOG.items():
        if not q or q in item_id or q in item["name"].lower() or q in item["category"].lower():
            cal_oz = item["calories_per_oz"]
            meets_ul_bar = cal_oz >= 125
            results.append({
                "id": item_id,
                "name": item["name"],
                "category": item["category"],
                "calories_per_oz": cal_oz,
                "caloric_efficiency": "Passes Ultralight Benchmark (>=125 cal/oz)" if meets_ul_bar else "Below benchmark (bulk weight penalty)",
                "macros_per_oz": {
                    "fat_g": item["fat_g_per_oz"],
                    "protein_g": item["protein_g_per_oz"],
                    "carbs_g": item["carbs_g_per_oz"]
                },
                "pricing": {
                    "typical_cost_per_lb": f"${item['typical_price_per_lb']:.2f}",
                    "cost_per_1000_calories": f"${item['price_per_1000_cal']:.2f}"
                },
                "notes": item["notes"]
            })

    if not results:
        return {
            "query": query,
            "message": "No exact match found in ultralight catalog. Showing all available ultralight staples.",
            "available_staples": list(ULTRALIGHT_SNACK_CATALOG.keys())
        }

    return {
        "query": query,
        "results_count": len(results),
        "snacks": results
    }


# ==============================================================================
# TRAIL IMAGE GENERATION TOOL (gemini-3.1-flash-lite-image)
# ==============================================================================

GCS_BUCKET_NAME = "bwg3-qwiklabs-gcp-03-c022e089199f"
IMAGE_MODEL_NAME = "gemini-3.1-flash-lite-image"
IMAGE_LOCATION = "global"

_genai_client = None
_gcs_client = None


def get_genai_image_client():
    global _genai_client
    if _genai_client is None:
        from google import genai
        _genai_client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location=IMAGE_LOCATION,
        )
    return _genai_client


def get_gcs_storage_client():
    global _gcs_client
    if _gcs_client is None:
        from google.cloud import storage
        _gcs_client = storage.Client(project=PROJECT_ID)
    return _gcs_client


async def generate_trail_image(
    trail_id: str,
    scene_description: str = "",
    tool_context: Optional[Any] = None,
) -> Dict[str, Any]:
    """Generate a photo-realistic visual preview of a trail or waypoint scene.

    Saves the image into ADK tool_context artifacts and uploads it directly to
    the public Cloud Storage bucket, returning the public HTTPS URL.

    Args:
        trail_id: Unique ID of the trail (e.g. 'enchantments-traverse', 'wonderland-trail-mt-rainier').
        scene_description: Optional custom scene prompt (e.g. 'sunrise over Colchuck Lake and Dragontail Peak').
        tool_context: ADK ToolContext injected by the agent runtime for artifact persistence.

    Returns:
        Public HTTPS Cloud Storage URL, filename, and image metadata.
    """
    from google.genai import types
    import uuid

    trail = get_trail_details(trail_id)
    trail_name = trail.get("name", trail_id)
    region = trail.get("region", "Washington Cascades")

    prompt = (
        f"A breathtaking, high-resolution landscape photograph of {trail_name} in {region}. "
        f"{scene_description if scene_description else trail.get('description', '')}. "
        "Crisp alpine light, towering glaciated peaks, pristine mountain lake, hyper-realistic, 8k resolution nature photography."
    )

    client = get_genai_image_client()
    response = client.models.generate_content(
        model=IMAGE_MODEL_NAME,
        contents=prompt,
    )

    image_bytes = None
    mime_type = "image/jpeg"

    if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if getattr(part, "inline_data", None) and part.inline_data.data:
                image_bytes = part.inline_data.data
                if part.inline_data.mime_type:
                    mime_type = part.inline_data.mime_type
                break

    if not image_bytes:
        return {"error": f"Failed to generate image bytes for trail '{trail_id}'"}

    safe_id = trail_id.replace(" ", "_").lower()
    unique_suffix = uuid.uuid4().hex[:8]
    filename = f"trail_{safe_id}_{unique_suffix}.jpg"

    # 1. Save with tool_context.save_artifact for Playground Artifacts panel
    if tool_context and hasattr(tool_context, "save_artifact"):
        try:
            artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            tool_context.save_artifact(
                filename=filename,
                artifact=artifact_part,
                custom_metadata={"trail_id": trail_id, "trail_name": trail_name, "model": IMAGE_MODEL_NAME}
            )
        except Exception as e:
            print(f"[Warning] tool_context.save_artifact failed: {e}")

    # 2. Upload image bytes to public Cloud Storage bucket
    gcs = get_gcs_storage_client()
    bucket = gcs.bucket(GCS_BUCKET_NAME)
    blob_path = f"trails/{filename}"
    blob = bucket.blob(blob_path)
    blob.upload_from_string(image_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{blob_path}"

    return {
        "status": "success",
        "trail_id": trail_id,
        "trail_name": trail_name,
        "filename": filename,
        "public_image_url": public_url,
        "content_type": mime_type,
        "size_bytes": len(image_bytes),
        "prompt_used": prompt,
    }
