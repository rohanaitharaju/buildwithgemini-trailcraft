"""Firestore tools for TrailCraft backpacking agent.

Provides read and write operations for 'trails' and 'gear' collections.
Uses hardcoded GCP project ID as a string to avoid project number issues on Agent Platform.
"""

from typing import Any, Dict, List, Optional
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-03-c022e089199f"
DATABASE_ID = "(default)"

_db: Optional[firestore.Client] = None


def get_firestore_client() -> firestore.Client:
    """Lazy initialize and return the Firestore client with hardcoded project ID."""
    global _db
    if _db is None:
        _db = firestore.Client(project=PROJECT_ID, database=DATABASE_ID)
    return _db


def list_trails(max_results: int = 10, max_difficulty: Optional[str] = None) -> List[Dict[str, Any]]:
    """List trails from the trail catalog.

    Args:
        max_results: Maximum number of trails to return (default 10).
        max_difficulty: Optional difficulty filter (e.g. 'Moderate', 'Challenging', 'Strenuous').

    Returns:
        A list of trail dictionaries containing name, distance, elevation, permits, water sources, etc.
    """
    db = get_firestore_client()
    trails_ref = db.collection("trails")
    docs = trails_ref.limit(max_results).stream()

    results = []
    for doc in docs:
        data = doc.to_dict()
        if max_difficulty and data.get("difficulty", "").lower() != max_difficulty.lower():
            continue
        results.append(data)
    return results


def get_trail_details(trail_id: str) -> Dict[str, Any]:
    """Retrieve detailed information about a specific trail by ID or name slug.

    Args:
        trail_id: The document ID of the trail (e.g., 'timberline-trail', 'four-pass-loop').

    Returns:
        A dictionary containing the trail details or an error message if not found.
    """
    db = get_firestore_client()
    doc = db.collection("trails").document(trail_id).get()
    if not doc.exists:
        return {"error": f"Trail with ID '{trail_id}' not found."}
    return doc.to_dict()


def save_trail(
    trail_id: str,
    name: str,
    region: str,
    distance_miles: float,
    elevation_gain_ft: int,
    difficulty: str,
    duration_days: int,
    permits_required: bool,
    permit_details: str,
    water_sources: List[str],
    offline_map_url: str = "",
    description: str = "",
) -> Dict[str, Any]:
    """Add or update a trail in the Firestore catalog.

    Args:
        trail_id: Unique identifier for the trail (e.g., 'wonderland-trail').
        name: Name of the trail or route.
        region: Geographic region or mountain range.
        distance_miles: Total trail distance in miles.
        elevation_gain_ft: Total elevation gain in feet.
        difficulty: Difficulty rating (e.g. 'Easy', 'Moderate', 'Challenging', 'Strenuous').
        duration_days: Estimated days for the backpacking trip.
        permits_required: True if permits are required, False otherwise.
        permit_details: Explanation of permit rules, lottery, or where to apply.
        water_sources: List of notable water points along the route.
        offline_map_url: URL to downloadable GPX or offline map.
        description: Summary overview of trail features and highlights.

    Returns:
        Status message with confirmation.
    """
    db = get_firestore_client()
    trail_data = {
        "id": trail_id,
        "name": name,
        "region": region,
        "distance_miles": distance_miles,
        "elevation_gain_ft": elevation_gain_ft,
        "difficulty": difficulty,
        "duration_days": duration_days,
        "permits_required": permits_required,
        "permit_details": permit_details,
        "water_sources": water_sources,
        "offline_map_url": offline_map_url,
        "description": description,
    }
    db.collection("trails").document(trail_id).set(trail_data)
    return {"status": "success", "message": f"Trail '{name}' ({trail_id}) successfully saved.", "trail": trail_data}


def list_gear_inventory(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """List gear items from the user's gear inventory.

    Args:
        category: Optional filter by category (e.g. 'Shelter', 'Sleep System', 'Water & Cooking', 'Safety', 'Food Storage').

    Returns:
        A list of gear items with weights and packing status.
    """
    db = get_firestore_client()
    gear_ref = db.collection("gear")
    docs = gear_ref.stream()

    items = []
    for doc in docs:
        item = doc.to_dict()
        if category and item.get("category", "").lower() != category.lower():
            continue
        items.append(item)
    return items


def add_or_update_gear_item(
    item_id: str,
    name: str,
    category: str,
    weight_oz: float,
    is_essential: bool = True,
    packed: bool = False,
    notes: str = "",
) -> Dict[str, Any]:
    """Add a new gear item or update an existing one in the inventory.

    Args:
        item_id: Unique identifier for the gear item (e.g., 'headlamp-nitecore-nu25').
        name: Name of the gear item.
        category: Category (e.g., 'Shelter', 'Sleep System', 'Clothing', 'Water & Cooking', 'Safety').
        weight_oz: Weight in ounces (crucial for base weight calculation).
        is_essential: Whether this item is mandatory for safety or comfort.
        packed: Whether the item is already packed in the backpack.
        notes: Helpful notes or usage instructions.

    Returns:
        Status message confirming the gear was saved.
    """
    db = get_firestore_client()
    gear_data = {
        "id": item_id,
        "name": name,
        "category": category,
        "weight_oz": weight_oz,
        "is_essential": is_essential,
        "packed": packed,
        "notes": notes,
    }
    db.collection("gear").document(item_id).set(gear_data)
    return {"status": "success", "message": f"Gear item '{name}' ({weight_oz} oz) saved.", "gear": gear_data}
