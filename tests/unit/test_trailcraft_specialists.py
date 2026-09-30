"""Unit tests for TrailCraft tools and multi-agent specialist functions."""

import pytest
from app.firestore_tools import list_trails, get_trail_details, list_gear_inventory
from app.specialist_tools import (
    calculate_pack_nutrition_and_water,
    fetch_trail_weather_and_conditions,
    get_permit_and_lottery_guidance,
)
from app.agent import (
    root_agent,
    weight_and_nutrition_specialist,
    weather_and_conditions_specialist,
    permits_and_logistics_specialist,
)


class TestFirestoreBackend:
    """Test Firestore trail catalog and gear inventory."""

    def test_top_20_washington_trails_populated(self):
        trails = list_trails(max_results=30)
        assert len(trails) >= 20, f"Expected at least 20 trails, got {len(trails)}"
        
        # Verify specific hard trail exists
        trail_ids = [t["id"] for t in trails]
        assert "enchantments-traverse" in trail_ids
        assert "wonderland-trail-mt-rainier" in trail_ids
        assert "spider-gap-buck-creek-pass-loop" in trail_ids

    def test_user_gear_kit(self):
        gear = list_gear_inventory()
        assert len(gear) >= 5, f"Expected at least 5 gear items, got {len(gear)}"

        gear_names = [g["name"] for g in gear]
        assert any("Arc'teryx Alpha" in name for name in gear_names)
        assert any("REI Co-op Flash Air" in name for name in gear_names)
        assert any("REI Co-op Magma" in name for name in gear_names)
        assert any("NEMO Tensor" in name for name in gear_names)
        assert any("No-Cook" in name for name in gear_names)


class TestWeightAndNutritionSpecialist:
    """Test calculations for ultralight pack, no-cook nutrition, and water strategy."""

    def test_calculate_pack_nutrition_and_water_enchantments(self):
        result = calculate_pack_nutrition_and_water("enchantments-traverse")
        assert "error" not in result
        
        # Base weight should reflect user's ~7.7 lbs kit
        assert 7.0 <= result["base_pack_weight_lbs"] <= 8.5
        
        # Verify food plan is tailored to no-cook
        food = result["food_plan"]
        assert food["strategy"] == "No-Cook / Cold Soak Ultralight"
        assert food["daily_calories"] == 3200
        assert food["total_food_weight_lbs"] > 0
        
        # Water carry should be optimized for plentiful sources in Enchantments
        water = result["water_strategy"]
        assert water["recommended_carry_liters"] <= 1.5
        assert "plentiful" in water["advice"].lower() or "frequent" in water["advice"].lower()
        
        # Total starting weight should be lightweight
        assert result["total_starting_pack_weight_lbs"] < 16.0

    def test_calculate_pack_nutrition_and_water_dry_route(self):
        # Mailbox peak has no reliable water on trail
        result = calculate_pack_nutrition_and_water("mailbox-peak-old-trail", custom_days=1)
        assert "error" not in result
        water = result["water_strategy"]
        assert water["recommended_carry_liters"] >= 2.0
        assert "dry" in water["advice"].lower() or "scarce" in water["advice"].lower()


class TestWeatherAndConditionsSpecialist:
    """Test live alpine weather data retrieval."""

    def test_fetch_live_trail_weather(self):
        weather = fetch_trail_weather_and_conditions("enchantments-traverse")
        assert "error" not in weather
        assert "temperature_f" in weather
        assert isinstance(weather["temperature_f"], (int, float))
        assert "wind_speed_mph" in weather
        assert "alpine_advisory" in weather
        assert len(weather["alpine_advisory"]) > 0


class TestPermitsAndLogisticsSpecialist:
    """Test wilderness permit guidance and quota links."""

    def test_enchantments_lottery_guidance(self):
        guidance = get_permit_and_lottery_guidance("enchantments-traverse")
        assert guidance["permits_required"] is True
        details = guidance["detailed_guidance"]
        assert "February 15 - March 1" in details["lottery_window"]
        assert "recreation.gov" in details["permit_portal"]
        assert "blue bags" in details["regulations"] or "toilets" in details["regulations"]

    def test_wonderland_permit_guidance(self):
        guidance = get_permit_and_lottery_guidance("wonderland-trail-mt-rainier")
        assert guidance["permits_required"] is True
        details = guidance["detailed_guidance"]
        assert "Mount Rainier" in details["zone"]
        assert "walk-up" in details["walk_up"].lower()


class TestMultiAgentStructure:
    """Test ADK root agent and sub-agent wiring."""

    def test_multiagent_hierarchy(self):
        assert root_agent.name == "root_agent"
        sub_names = [s.name for s in root_agent.sub_agents]
        assert "weight_and_nutrition_specialist" in sub_names
        assert "weather_and_conditions_specialist" in sub_names
        assert "permits_and_logistics_specialist" in sub_names

        # Verify tool registrations
        assert calculate_pack_nutrition_and_water in weight_and_nutrition_specialist.tools
        assert fetch_trail_weather_and_conditions in weather_and_conditions_specialist.tools
        assert get_permit_and_lottery_guidance in permits_and_logistics_specialist.tools


class TestDaylightPublicAPI:
    """Test integration with Sunrise-Sunset public API."""

    def test_get_trail_daylight_and_sun_times(self):
        from app.specialist_tools import get_trail_daylight_and_sun_times
        daylight = get_trail_daylight_and_sun_times("enchantments-traverse")
        assert "error" not in daylight
        assert "sunrise" in daylight
        assert "sunset" in daylight
        assert "first_usable_light" in daylight
        assert "last_usable_light" in daylight
        assert daylight["total_daylight_hours"] > 0
        assert "PDT" in daylight["sunrise"] or "PST" in daylight["sunrise"]


class TestNavigationAndSnackTools:
    """Test offline navigation maps and snack nutrition/pricing lookup."""

    def test_get_trailhead_navigation_and_offline_map(self):
        from app.specialist_tools import get_trailhead_navigation_and_offline_map
        nav = get_trailhead_navigation_and_offline_map("enchantments-traverse")
        assert "error" not in nav
        assert "trailhead" in nav
        assert "google_maps_driving_url" in nav["trailhead"]
        assert "offline_navigation" in nav
        assert "caltopo_interactive_topo" in nav["offline_navigation"]
        assert "gpx_direct_download" in nav["offline_navigation"]

    def test_lookup_ultralight_trail_snack(self):
        from app.specialist_tools import lookup_ultralight_trail_snack
        res = lookup_ultralight_trail_snack("macadamia")
        assert res["results_count"] >= 1
        item = res["snacks"][0]
        assert item["calories_per_oz"] >= 125
        assert "Passes Ultralight Benchmark" in item["caloric_efficiency"]
        assert "$" in item["pricing"]["typical_cost_per_lb"]
        assert "$" in item["pricing"]["cost_per_1000_calories"]


class TestTrailImageGeneration:
    """Test image generation using gemini-3.1-flash-lite-image and GCS upload."""

    @pytest.mark.asyncio
    async def test_generate_trail_image_and_upload(self):
        from app.specialist_tools import generate_trail_image
        
        # Test mock tool context for save_artifact
        class MockToolContext:
            def __init__(self):
                self.saved = False
            def save_artifact(self, filename, artifact, custom_metadata=None):
                self.saved = True
                return 1

        mock_ctx = MockToolContext()
        res = await generate_trail_image("colchuck-lake", "Turquoise glacial water under Dragontail Peak", tool_context=mock_ctx)
        
        assert res["status"] == "success"
        assert mock_ctx.saved is True
        assert "public_image_url" in res
        assert "https://storage.googleapis.com/bwg3-qwiklabs-gcp-03-c022e089199f/trails/" in res["public_image_url"]
        assert res["size_bytes"] > 50000


class TestAgentEngineSandbox:
    """Test AgentEngineSandboxCodeExecutor configuration and attachment."""

    def test_root_agent_code_executor_configured(self):
        from app.agent import root_agent
        from google.adk.code_executors import AgentEngineSandboxCodeExecutor

        assert root_agent.code_executor is not None
        assert isinstance(root_agent.code_executor, AgentEngineSandboxCodeExecutor)
        assert "6544466931359940608" in root_agent.code_executor.agent_engine_resource_name
