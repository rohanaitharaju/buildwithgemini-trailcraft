#!/usr/bin/env python3
"""Seed script for TrailCraft Firestore backend.

Populates initial trail catalog and gear inventory collections.
"""

from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-03-c022e089199f"
DATABASE_ID = "(default)"

SAMPLE_TRAILS = [
    {
        "id": "john-muir-trail-section",
        "name": "John Muir Trail - Thousand Island Lake Loop",
        "region": "Sierra Nevada, CA",
        "distance_miles": 23.5,
        "elevation_gain_ft": 3800,
        "difficulty": "Challenging",
        "duration_days": 3,
        "permits_required": True,
        "permit_details": "Inyo National Forest wilderness permit required during peak season (quota system).",
        "water_sources": ["Rush Creek", "Garnet Lake", "Thousand Island Lake", "Shadow Creek"],
        "recommended_pack_type": "Ultralight / Lightweight",
        "offline_map_url": "https://maps.google.com/sample/jmt_thousand_island_offline.gpx",
        "description": "Epic alpine loop visiting stunning granite lakes under Mt. Ritter and Banner Peak."
    },
    {
        "id": "timberline-trail",
        "name": "Timberline Trail around Mt. Hood",
        "region": "Mount Hood Wilderness, OR",
        "distance_miles": 41.5,
        "elevation_gain_ft": 9000,
        "difficulty": "Strenuous",
        "duration_days": 4,
        "permits_required": True,
        "permit_details": "Free self-issued wilderness permit at trailhead (May 15 - Oct 15).",
        "water_sources": ["Eliot Branch", "Cloud Cap", "Muddy Fork", "Sandy River"],
        "recommended_pack_type": "Lightweight",
        "offline_map_url": "https://maps.google.com/sample/timberline_trail_offline.gpx",
        "description": "Circumnavigates Mt. Hood featuring alpine meadows, glacial river crossings, and rugged climbs."
    },
    {
        "id": "four-pass-loop",
        "name": "Four Pass Loop",
        "region": "Maroon Bells-Snowmass Wilderness, CO",
        "distance_miles": 28.0,
        "elevation_gain_ft": 7750,
        "difficulty": "Challenging",
        "duration_days": 3,
        "permits_required": True,
        "permit_details": "Overnight permit required via Recreation.gov for Maroon Bells-Snowmass zones.",
        "water_sources": ["Crater Lake", "West Maroon Creek", "Snowmass Lake"],
        "recommended_pack_type": "Ultralight",
        "offline_map_url": "https://maps.google.com/sample/four_pass_loop_offline.gpx",
        "description": "Breathtaking Rocky Mountain traverse crossing 4 passes over 12,000 feet."
    },
    {
        "id": "kesugi-ridge",
        "name": "Kesugi Ridge Trail",
        "region": "Denali State Park, AK",
        "distance_miles": 29.2,
        "elevation_gain_ft": 6000,
        "difficulty": "Moderate to Strenuous",
        "duration_days": 3,
        "permits_required": False,
        "permit_details": "No permits required. Bear canister mandatory.",
        "water_sources": ["Troublesome Creek", "Skinny Lake", "Byers Lake"],
        "recommended_pack_type": "Lightweight / Expedition",
        "offline_map_url": "https://maps.google.com/sample/kesugi_ridge_offline.gpx",
        "description": "Expansive alpine ridge hike with panoramic views of Denali on clear days."
    }
]

SAMPLE_GEAR = [
    {
        "id": "tent-durston-xmid2",
        "name": "Durston X-Mid 2 Trekking Pole Tent",
        "category": "Shelter",
        "weight_oz": 36.0,
        "is_essential": True,
        "packed": False,
        "notes": "Requires 2 trekking poles. Excellent storm resistance."
    },
    {
        "id": "quilt-enlightened-equipment-20",
        "name": "Enlightened Equipment Revelation 20° Quilt",
        "category": "Sleep System",
        "weight_oz": 22.5,
        "is_essential": True,
        "packed": False,
        "notes": "850 fill down, comfortable down to 25°F."
    },
    {
        "id": "filter-sawyer-squeeze",
        "name": "Sawyer Squeeze Water Filter",
        "category": "Water & Cooking",
        "weight_oz": 3.0,
        "is_essential": True,
        "packed": False,
        "notes": "Includes dirty water bladder and coupling adapter."
    },
    {
        "id": "stove-brs-3000t",
        "name": "BRS-3000T Ultralight Canister Stove",
        "category": "Water & Cooking",
        "weight_oz": 0.9,
        "is_essential": True,
        "packed": False,
        "notes": "Minimalist titanium stove for boiling water."
    },
    {
        "id": "bear-canister-bv450",
        "name": "BearVault BV450 Solo Food Canister",
        "category": "Food Storage",
        "weight_oz": 33.0,
        "is_essential": True,
        "packed": False,
        "notes": "Holds 3-4 days of dehydrated meals. Required in Sierra & Denali."
    },
    {
        "id": "first-aid-ultralight",
        "name": "Ultralight First Aid & Repair Kit",
        "category": "Safety",
        "weight_oz": 4.5,
        "is_essential": True,
        "packed": False,
        "notes": "Leukotape, ibuprofen, alcohol wipes, Tenacious Tape, water purification tabs."
    }
]


def seed_database():
    print(f"Connecting to Firestore for project '{PROJECT_ID}'...")
    db = firestore.Client(project=PROJECT_ID, database=DATABASE_ID)

    print("Seeding 'trails' collection...")
    trails_ref = db.collection("trails")
    for trail in SAMPLE_TRAILS:
        doc_id = trail["id"]
        trails_ref.document(doc_id).set(trail)
        print(f"  ✓ Added trail: {trail['name']} ({doc_id})")

    print("\nSeeding 'gear' collection...")
    gear_ref = db.collection("gear")
    for item in SAMPLE_GEAR:
        doc_id = item["id"]
        gear_ref.document(doc_id).set(item)
        print(f"  ✓ Added gear: {item['name']} ({item['weight_oz']} oz)")

    print("\nFirestore seeding complete! Both 'trails' and 'gear' collections are populated.")


if __name__ == "__main__":
    seed_database()
