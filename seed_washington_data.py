#!/usr/bin/env python3
"""Seed script for TrailCraft with Washington state popular trails and user's specific gear."""

from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-03-c022e089199f"
DATABASE_ID = "(default)"

WASHINGTON_TOP_20_TRAILS = [
    {
        "id": "enchantments-traverse",
        "name": "The Enchantments Thru-Hike",
        "region": "Alpine Lakes Wilderness, Central Cascades, WA",
        "distance_miles": 19.5,
        "elevation_gain_ft": 4500,
        "difficulty": "Hard",
        "duration_days": 2,
        "permits_required": True,
        "permit_details": "Strict lottery permit required for overnight camping May 15 - Oct 31 via Recreation.gov. Day use requires self-issue permit.",
        "water_sources": ["Colchuck Lake", "Inspiration Lake", "Perfection Lake", "Snow Lakes", "Nada Lake"],
        "recommended_pack_type": "Ultralight",
        "offline_map_url": "https://www.wta.org/go-hiking/hikes/enchantment-lakes",
        "description": "Legendary alpine traverse passing crystal blue tarns, granite spires, Aasgard Pass, and resident mountain goats."
    },
    {
        "id": "wonderland-trail-mt-rainier",
        "name": "Wonderland Trail",
        "region": "Mount Rainier National Park, WA",
        "distance_miles": 93.0,
        "elevation_gain_ft": 24000,
        "difficulty": "Hard",
        "duration_days": 9,
        "permits_required": True,
        "permit_details": "Wilderness permit required for all backcountry camps via Mount Rainier NP lottery / Recreation.gov.",
        "water_sources": ["White River", "Carbon River", "Mowich Lake", "Mowich River", "Golden Lakes", "Nickel Creek"],
        "recommended_pack_type": "Lightweight / Ultralight",
        "offline_map_url": "https://www.nps.gov/mora/planyourvisit/the-wonderland-trail.htm",
        "description": "Iconic circumnavigation of Mount Rainier traversing glaciers, alpine valleys, ancient forests, and rushing glacial melt rivers."
    },
    {
        "id": "spider-gap-buck-creek-pass-loop",
        "name": "Spider Gap - Buck Creek Pass Loop",
        "region": "Glacier Peak Wilderness, North Cascades, WA",
        "distance_miles": 44.0,
        "elevation_gain_ft": 8100,
        "difficulty": "Hard",
        "duration_days": 4,
        "permits_required": False,
        "permit_details": "Free self-issued wilderness permit at trailhead. Northwest Forest Pass required to park.",
        "water_sources": ["Phelps Creek", "Spider Meadow", "Lyman Lakes", "Miners Creek", "Buck Creek"],
        "recommended_pack_type": "Ultralight",
        "offline_map_url": "https://www.wta.org/go-hiking/hikes/spider-gap-buck-creek-pass-loop",
        "description": "Glacier crossing over Spider Glacier snowfield, stunning Lyman Lakes, and panoramic flower meadows at Buck Creek Pass."
    },
    {
        "id": "mount-olympus-hoh-river-trail",
        "name": "Mount Olympus via Hoh River Trail",
        "region": "Olympic National Park, WA",
        "distance_miles": 37.0,
        "elevation_gain_ft": 4300,
        "difficulty": "Hard",
        "duration_days": 4,
        "permits_required": True,
        "permit_details": "Olympic National Park wilderness camping permit required year-round via Recreation.gov. Bear canister mandatory.",
        "water_sources": ["Hoh River", "Olympus Guard Station", "Lewis Meadow", "Glacier Meadows"],
        "recommended_pack_type": "Lightweight",
        "offline_map_url": "https://www.nps.gov/olym/planyourvisit/wilderness-trip-planner.htm",
        "description": "Hike through lush temperate rainforest along the Hoh River before steep climbing to Blue Glacier under Mount Olympus."
    },
    {
        "id": "ptarmigan-traverse",
        "name": "Ptarmigan Traverse (Cascade Pass to Downey Creek)",
        "region": "North Cascades National Park & Glacier Peak Wilderness, WA",
        "distance_miles": 35.0,
        "elevation_gain_ft": 13000,
        "difficulty": "Hard",
        "duration_days": 5,
        "permits_required": True,
        "permit_details": "Wilderness permit required within North Cascades National Park boundaries (Marblemount Ranger Station).",
        "water_sources": ["Pelton Basin", "Kool-Aid Lake", "Yang Yang Lakes", "Cub Lake", "Downey Creek"],
        "recommended_pack_type": "Ultralight / Mountaineering",
        "offline_map_url": "https://www.wta.org/go-hiking/hikes/ptarmigan-traverse",
        "description": "America's premier high alpine wilderness traverse over glaciers, rugged cols, and remote off-trail alpine terrain."
    },
    {
        "id": "mailbox-peak-old-trail",
        "name": "Mailbox Peak (Old Trail)",
        "region": "North Bend, Snoqualmie Region, WA",
        "distance_miles": 5.4,
        "elevation_gain_ft": 4000,
        "difficulty": "Hard",
        "duration_days": 1,
        "permits_required": False,
        "permit_details": "Discover Pass required for parking at the trailhead.",
        "water_sources": ["No reliable water sources - carry all water needed (3+ Liters)."],
        "recommended_pack_type": "Ultralight Daypack",
        "offline_map_url": "https://www.wta.org/go-hiking/hikes/mailbox-peak-old-trail",
        "description": "Washington's legendary steep conditioning test gaining 4,000 feet in just 2.7 miles to the iconic summit mailbox."
    },
    {
        "id": "mount-si-via-old-mount-si",
        "name": "Mount Si / Old Mount Si Trail",
        "region": "North Bend, Snoqualmie Region, WA",
        "distance_miles": 8.0,
        "elevation_gain_ft": 3150,
        "difficulty": "Hard",
        "duration_days": 1,
        "permits_required": False,
        "permit_details": "Discover Pass required for trailhead parking.",
        "water_sources": ["Snag Flat stream (seasonal), carry all drinking water."],
        "recommended_pack_type": "Ultralight Daypack",
        "offline_map_url": "https://www.wta.org/go-hiking/hikes/mount-si",
        "description": "Classic Pacific Northwest summit hike delivering sweeping views of Mount Rainier and the Snoqualmie Valley."
    },
    {
        "id": "mount-st-helens-monitor-ridge",
        "name": "Mount St. Helens Summit (Monitor Ridge)",
        "region": "Mount St. Helens National Volcanic Monument, WA",
        "distance_miles": 10.0,
        "elevation_gain_ft": 4500,
        "difficulty": "Hard",
        "duration_days": 1,
        "permits_required": True,
        "permit_details": "Climbing permit required above 4,800 ft year-round. Quota permit via Recreation.gov April 1 - October 31.",
        "water_sources": ["None along route. Bring minimum 3-4 liters."],
        "recommended_pack_type": "Daypack / Scramble",
        "offline_map_url": "https://www.fs.usda.gov/recarea/giffordpinchot/recarea/?recid=31584",
        "description": "Scramble across boulder fields and ash scree to peer over the crater rim directly into the active lava dome."
    },
    {
        "id": "gothic-basin",
        "name": "Gothic Basin and Foggy Lake",
        "region": "Mountain Loop Highway, North Cascades, WA",
        "distance_miles": 9.2,
        "elevation_gain_ft": 2840,
        "difficulty": "Hard",
        "duration_days": 2,
        "permits_required": False,
        "permit_details": "Northwest Forest Pass or America the Beautiful Pass required to park.",
        "water_sources": ["Wedgemount Creek", "Gothic Basin tarns", "Foggy Lake"],
        "recommended_pack_type": "Ultralight",
        "offline_map_url": "https://www.wta.org/go-hiking/hikes/gothic-basin",
        "description": "Steep rocky trail up historical mining ruins to a high alpine basin of polished granite and glacial tarns."
    },
    {
        "id": "sahale-arm-cascade-pass",
        "name": "Sahale Arm and Cascade Pass",
        "region": "North Cascades National Park, WA",
        "distance_miles": 12.0,
        "elevation_gain_ft": 4000,
        "difficulty": "Hard",
        "duration_days": 2,
        "permits_required": True,
        "permit_details": "Backcountry permit required for camping at Sahale Glacier Camp or Pelton Basin (in-person at Marblemount).",
        "water_sources": ["Cascade Pass basin runoff", "Sahale Glacier melt streams"],
        "recommended_pack_type": "Ultralight",
        "offline_map_url": "https://www.wta.org/go-hiking/hikes/sahale-arm",
        "description": "Unrivaled 360-degree glaciated peaks. Sahale Glacier Camp is perched high on rocky moraines overlooking Doubtful Lake."
    },
    {
        "id": "lake-ingalls-esmeralda-basin",
        "name": "Lake Ingalls via Esmeralda Basin",
        "region": "Teanaway / Alpine Lakes Wilderness, WA",
        "distance_miles": 9.0,
        "elevation_gain_ft": 2800,
        "difficulty": "Hard",
        "duration_days": 2,
        "permits_required": False,
        "permit_details": "Day hike free self-issue. Camping permitted in Ingalls Pass/Headlight Basin (no camping right on lake shore). Northwest Forest Pass.",
        "water_sources": ["North Fork Teanaway River", "Headlight Creek", "Lake Ingalls"],
        "recommended_pack_type": "Ultralight",
        "offline_map_url": "https://www.wta.org/go-hiking/hikes/lake-ingalls",
        "description": "Vibrant golden larches in autumn, granite rock scrambles, and the immense south face of Mount Stuart reflected in indigo water."
    },
    {
        "id": "lake-serene-bridal-veil-falls",
        "name": "Lake Serene and Bridal Veil Falls",
        "region": "Central Cascades / Stevens Pass, WA",
        "distance_miles": 8.2,
        "elevation_gain_ft": 2000,
        "difficulty": "Hard",
        "duration_days": 1,
        "permits_required": False,
        "permit_details": "Northwest Forest Pass required for parking.",
        "water_sources": ["Bridal Veil Creek", "Lake Serene"],
        "recommended_pack_type": "Ultralight Daypack",
        "offline_map_url": "https://www.wta.org/go-hiking/hikes/lake-serene",
        "description": "Steep wooden staircases and relentless switchbacks climbing to Lunch Rock beneath the vertical cliffs of Mount Index."
    },
    {
        "id": "colchuck-lake",
        "name": "Colchuck Lake Trail",
        "region": "Alpine Lakes Wilderness, Leavenworth, WA",
        "distance_miles": 8.0,
        "elevation_gain_ft": 2280,
        "difficulty": "Hard",
        "duration_days": 1,
        "permits_required": True,
        "permit_details": "Day use free self-issue at trailhead. Overnight requires Enchantments core lottery permit.",
        "water_sources": ["Mountaineer Creek", "Colchuck Lake"],
        "recommended_pack_type": "Ultralight",
        "offline_map_url": "https://www.wta.org/go-hiking/hikes/colchuck-lake",
        "description": "Gateway to the Enchantments, featuring turquoise glacial waters beneath Dragontail Peak and Colchuck Peak."
    },
    {
        "id": "granite-mountain-lookout",
        "name": "Granite Mountain Trail & Fire Lookout",
        "region": "Snoqualmie Pass, WA",
        "distance_miles": 8.6,
        "elevation_gain_ft": 3800,
        "difficulty": "Hard",
        "duration_days": 1,
        "permits_required": False,
        "permit_details": "Northwest Forest Pass required at Pratt Lake / Granite Mountain trailhead.",
        "water_sources": ["Lower avalanche creek only (carry all summit water)."],
        "recommended_pack_type": "Ultralight Daypack",
        "offline_map_url": "https://www.wta.org/go-hiking/hikes/granite-mountain",
        "description": "Unforgiving climb through open avalanche chutes up to a functioning historic fire lookout with panoramic Cascade views."
    },
    {
        "id": "goat-rocks-wilderness-cispus-basin-snowgrass",
        "name": "Goat Rocks Wilderness: Snowgrass Flats & Cispus Basin Loop",
        "region": "Goat Rocks Wilderness, South Cascades, WA",
        "distance_miles": 21.0,
        "elevation_gain_ft": 4200,
        "difficulty": "Hard",
        "duration_days": 3,
        "permits_required": False,
        "permit_details": "Free self-issued wilderness permit at Berry Patch / Snowgrass trailhead. Northwest Forest Pass required.",
        "water_sources": ["Goat Creek", "Snowgrass Springs", "Cispus Basin streams"],
        "recommended_pack_type": "Ultralight",
        "offline_map_url": "https://www.wta.org/go-hiking/hikes/cispus-basin-snowgrass-flats-loop",
        "description": "One of the Pacific Crest Trail's most scenic sections, crossing knife-edge ridges with views of Rainier, Adams, and St. Helens."
    },
    {
        "id": "mount-adams-south-climb",
        "name": "Mount Adams South Climb",
        "region": "Mount Adams Wilderness, Gifford Pinchot NF, WA",
        "distance_miles": 12.0,
        "elevation_gain_ft": 6700,
        "difficulty": "Hard",
        "duration_days": 2,
        "permits_required": True,
        "permit_details": "Cascades Volcano Pass required above 7,000 ft from May 1 to Sept 30.",
        "water_sources": ["Morrison Creek at trailhead, snowmelt at Lunch Counter (must filter/treat)."],
        "recommended_pack_type": "Mountaineering / Ultralight",
        "offline_map_url": "https://www.fs.usda.gov/recarea/giffordpinchot/recarea/?recid=31522",
        "description": "Non-technical volcano summit climb with overnight camping at Lunch Counter and exciting glissading on the descent."
    },
    {
        "id": "blanca-lake",
        "name": "Blanca Lake Trail",
        "region": "Wild Sky Wilderness, Central Cascades, WA",
        "distance_miles": 7.5,
        "elevation_gain_ft": 3300,
        "difficulty": "Hard",
        "duration_days": 1,
        "permits_required": False,
        "permit_details": "Northwest Forest Pass required at trailhead.",
        "water_sources": ["Virgin Lake, Blanca Lake outlet stream"],
        "recommended_pack_type": "Ultralight Daypack",
        "offline_map_url": "https://www.wta.org/go-hiking/hikes/blanca-lake",
        "description": "Challenging switchbacks through old growth forest, passing Virgin Lake before dropping to surreal milky-turquoise Blanca Lake."
    },
    {
        "id": "yellow-aster-butte",
        "name": "Yellow Aster Butte",
        "region": "Mount Baker Wilderness, North Cascades, WA",
        "distance_miles": 7.5,
        "elevation_gain_ft": 2550,
        "difficulty": "Hard",
        "duration_days": 2,
        "permits_required": False,
        "permit_details": "Free self-issued wilderness permit at trailhead. Northwest Forest Pass required.",
        "water_sources": ["High tarn basins below the butte (seasonal snowmelt)."],
        "recommended_pack_type": "Ultralight",
        "offline_map_url": "https://www.wta.org/go-hiking/hikes/yellow-aster-butte",
        "description": "Vibrant wildflowers, autumn blueberries, high alpine tarns, and face-to-face views of Mount Baker and Mount Shuksan."
    },
    {
        "id": "lake-constance",
        "name": "Lake Constance Trail",
        "region": "Olympic National Park, WA",
        "distance_miles": 4.0,
        "elevation_gain_ft": 3400,
        "difficulty": "Hard",
        "duration_days": 2,
        "permits_required": True,
        "permit_details": "Olympic National Park wilderness permit required (quota zone). Hand-and-foot scrambling required.",
        "water_sources": ["Dosewallips River, Lake Constance"],
        "recommended_pack_type": "Ultralight",
        "offline_map_url": "https://www.nps.gov/olym/planyourvisit/lake-constance-trail.htm",
        "description": "Infamous Olympic vertical scramble gaining nearly 1,000 feet per mile up steep roots, rock chimneys, and avalanche chutes."
    },
    {
        "id": "maple-pass-loop",
        "name": "Heather - Maple Pass Loop",
        "region": "North Cascades / Highway 20, WA",
        "distance_miles": 7.2,
        "elevation_gain_ft": 2020,
        "difficulty": "Hard",
        "duration_days": 1,
        "permits_required": False,
        "permit_details": "Northwest Forest Pass required at Rainy Pass picnic area.",
        "water_sources": ["Lake Ann runoff stream (lower section only)"],
        "recommended_pack_type": "Ultralight Daypack",
        "offline_map_url": "https://www.wta.org/go-hiking/hikes/maple-pass",
        "description": "Pound-for-pound Washington's most scenic loop trail with views of Lake Ann, Glacier Peak, and golden larches."
    }
]

USER_HIKING_GEAR = [
    {
        "id": "pack-arcteryx-alpha-ar-55",
        "name": "Arc'teryx Alpha AR 55L Backpack",
        "category": "Pack",
        "weight_oz": 48.0,
        "is_essential": True,
        "packed": True,
        "notes": "Custom lightweight alpine expedition pack. Highly durable Hadron LCP fabric."
    },
    {
        "id": "shelter-rei-ultralight-tent",
        "name": "REI Co-op Flash Air Ultralight Tent",
        "category": "Shelter",
        "weight_oz": 30.0,
        "is_essential": True,
        "packed": False,
        "notes": "Ultralight single-wall non-freestanding shelter pitched with trekking poles."
    },
    {
        "id": "sleeping-bag-rei-ultralight",
        "name": "REI Co-op Magma Ultralight Down Sleeping Bag",
        "category": "Sleep System",
        "weight_oz": 24.0,
        "is_essential": True,
        "packed": False,
        "notes": "850-fill power water-resistant goose down. Tested comfort for alpine nights."
    },
    {
        "id": "pad-nemo-tensor-ultralight",
        "name": "NEMO Tensor Ultralight Insulated Sleeping Pad",
        "category": "Sleep System",
        "weight_oz": 14.5,
        "is_essential": True,
        "packed": False,
        "notes": "3 inches of quiet, insulated cushion. R-value 4.2."
    },
    {
        "id": "safety-first-aid-kit",
        "name": "Ultralight & Watertight First Aid Kit",
        "category": "Safety",
        "weight_oz": 5.0,
        "is_essential": True,
        "packed": False,
        "notes": "Trauma supplies, blister treatment (moleskin/leukotape), bandages, antiseptic, pain relievers."
    },
    {
        "id": "food-strategy-cold-soak-no-cook",
        "name": "No-Cook / Cold-Soak Food Setup",
        "category": "Nutrition Strategy",
        "weight_oz": 2.0,
        "is_essential": True,
        "packed": False,
        "notes": "No cooking supplies or stove carried. Ready-to-eat calorie-dense foods (bars, nuts, jerky, nut butters, cold-soak)."
    }
]


def populate():
    print(f"Connecting to Firestore for project '{PROJECT_ID}'...")
    db = firestore.Client(project=PROJECT_ID, database=DATABASE_ID)

    print("\nPopulating top 20 Washington trails (Hard difficulty)...")
    trails_ref = db.collection("trails")
    for trail in WASHINGTON_TOP_20_TRAILS:
        trails_ref.document(trail["id"]).set(trail)
        print(f"  ✓ [{trail['difficulty']}] {trail['name']} ({trail['distance_miles']} mi, +{trail['elevation_gain_ft']} ft)")

    print("\nPopulating user's specific gear kit...")
    gear_ref = db.collection("gear")
    
    # Clean previous demo gear items first
    existing_docs = gear_ref.stream()
    for doc in existing_docs:
        doc.reference.delete()

    for item in USER_HIKING_GEAR:
        gear_ref.document(item["id"]).set(item)
        print(f"  ✓ {item['name']} ({item['category']} - {item['weight_oz']} oz)")

    print("\nWashington trails & personalized gear kit successfully populated in Firestore!")


if __name__ == "__main__":
    populate()
