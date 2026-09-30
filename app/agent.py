# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import json
import os
from pathlib import Path
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.genai import types

from app.firestore_tools import (
    add_or_update_gear_item,
    get_trail_details,
    list_gear_inventory,
    list_trails,
    save_trail,
)
from app.specialist_tools import (
    calculate_pack_nutrition_and_water,
    fetch_trail_weather_and_conditions,
    generate_trail_image,
    get_permit_and_lottery_guidance,
    get_trail_daylight_and_sun_times,
    get_trailhead_navigation_and_offline_map,
    lookup_ultralight_trail_snack,
)

MODEL = "gemini-3.6-flash"


def get_current_time(query: str = "PST") -> str:
    """Gets current Pacific Standard/Daylight time for trail planning."""
    tz = ZoneInfo("America/Los_Angeles")
    now = datetime.datetime.now(tz)
    return f"Current Pacific Time: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}"


# ==============================================================================
# SPECIALIST SUB-AGENTS (Multi-Agent Architecture)
# ==============================================================================

weight_and_nutrition_specialist = Agent(
    name="weight_and_nutrition_specialist",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are the Ultralight Weight & Nutrition Specialist for TrailCraft. "
        "You analyze trail difficulty, mileage, and elevation gain to optimize pack base weight, "
        "tailor no-cook/cold-soak calorie-dense nutrition plans (targeting >=125 cal/oz), "
        "look up snack calorie densities, macros, and prices per 1000 calories via 'lookup_ultralight_trail_snack', "
        "and calculate exact water carry amounts between trail water sources to prevent hauling excess weight. "
        "You calculate estimated hiking times using Naismith's rule adjusted for steep alpine terrain."
    ),
    tools=[
        calculate_pack_nutrition_and_water,
        lookup_ultralight_trail_snack,
        list_gear_inventory,
        add_or_update_gear_item,
    ],
)

weather_and_conditions_specialist = Agent(
    name="weather_and_conditions_specialist",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are the Alpine Mountain Weather, Daylight & Trail Safety Specialist for TrailCraft. "
        "You retrieve live atmospheric conditions, ridge winds, temperatures, precipitation, and freeze levels "
        "for Washington alpine passes and high wilderness trails. "
        "You also retrieve sunrise, sunset, first light, last light, and daylight hours using the Sunrise-Sunset API "
        "so hikers can plan alpine starts and clear technical scramble passes before dark. "
        "You advise hikers on required safety insulation, tent pitching cautions, and lighting requirements."
    ),
    tools=[fetch_trail_weather_and_conditions, get_trail_daylight_and_sun_times],
)

permits_and_logistics_specialist = Agent(
    name="permits_and_logistics_specialist",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are the Wilderness Permits, Navigation & Land Agency Specialist for TrailCraft. "
        "You provide precise guidance on Washington wilderness permits, quota lottery dates, "
        "walk-up availability (Mount Rainier, Enchantments, North Cascades, Mount St. Helens, Olympics), "
        "required bear canister regulations, direct Recreation.gov links, "
        "and trailhead driving directions with downloadable offline CalTopo/Gaia GPX map tracks via 'get_trailhead_navigation_and_offline_map'."
    ),
    tools=[
        get_permit_and_lottery_guidance,
        get_trailhead_navigation_and_offline_map,
        get_trail_details,
    ],
)


# ==============================================================================
# AGENT ENGINE CODE EXECUTION SANDBOX
# ==============================================================================

def _get_agent_engine_resource_name() -> str:
    metadata_path = Path(__file__).parent.parent / "deployment_metadata.json"
    if metadata_path.exists():
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("remote_agent_runtime_id", "")
        except Exception:
            pass
    return "projects/466224497514/locations/us-east1/reasoningEngines/6544466931359940608"

AGENT_ENGINE_ID = _get_agent_engine_resource_name()
sandbox_code_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=AGENT_ENGINE_ID
)


# ==============================================================================
# ROOT ORCHESTRATOR AGENT
# ==============================================================================

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are TrailCraft, an elite backpacking and trail planning expedition concierge. "
        "You assist experienced hikers who tackle hard Washington trails with an ultralight, no-cook setup. "
        "You have access to a database of Washington's top 20 premier trails and the user's gear inventory. "
        "You have code execution enabled via a secure sandbox to perform complex calculations, "
        "calorie burn analysis, elevation profile grade simulations, or pack weight modeling in Python. "
        "IMPORTANT: When generating a trip itinerary, you MUST proactively call 'get_trailhead_navigation_and_offline_map' "
        "and explicitly include the CalTopo GPX URL and Google Maps navigation URL in your final output so the frontend can render map buttons. "
        "Delegate specialized tasks to your sub-agents:\n"
        "- Delegate weight, calories, snack lookup/pricing, and water math to 'weight_and_nutrition_specialist'.\n"
        "- Delegate live weather, wind, alpine safety, and daylight hours to 'weather_and_conditions_specialist'.\n"
        "- Delegate lottery dates, permits, trailhead navigation, and offline GPX maps to 'permits_and_logistics_specialist'.\n"
        "Synthesize their outputs into a cohesive, concise, high-value expedition plan."
    ),
    code_executor=sandbox_code_executor,
    tools=[
        list_trails,
        get_trail_details,
        get_trailhead_navigation_and_offline_map,
        generate_trail_image,
        save_trail,
        get_current_time,
    ],
    sub_agents=[
        weight_and_nutrition_specialist,
        weather_and_conditions_specialist,
        permits_and_logistics_specialist,
    ],
)

app = App(
    root_agent=root_agent,
    name="app",
)
