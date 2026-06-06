from app.agents.hulk import HulkAgent
from app.memory.workout_store import WorkoutStore
from app.planning.plan_store import WorkoutPlanStore
from app.tools.models import ToolResult


class FakeGroqClient:
    def __init__(self):
        self.calls = []

    async def chat(self, messages, temperature=0.4, max_tokens=700):
        self.calls.append(messages)
        return "Hulk final"


class FakeHulkTools:
    def __init__(self):
        self.food_queries = []
        self.research_queries = []

    async def get_taiwan_food_info(self, food_name):
        self.food_queries.append(food_name)
        return ToolResult(
            name="get_taiwan_food_info",
            query=food_name,
            content="Food lookup context",
            sources=["https://example.com/food"],
        )

    async def get_scientific_workout_research(self, workout_topic):
        self.research_queries.append(workout_topic)
        return ToolResult(
            name="get_scientific_workout_research",
            query=workout_topic,
            content="Research context",
            sources=["https://example.com/research"],
        )


class FakePhysiqueAnalyzer:
    def __init__(self):
        self.calls = []

    async def analyze_physique(self, attachment, context=""):
        self.calls.append((attachment, context))
        return "Physique analysis"


class FakeImageAnalyzer:
    def __init__(self):
        self.calls = []

    async def analyze_image(self, attachment, context=""):
        self.calls.append((attachment, context))
        return "Food check:\nEstimate: 600-750 kcal\nPlease confirm: portion size?"


async def test_hulk_logs_workout_and_injects_recent_history(tmp_path):
    groq_client = FakeGroqClient()
    store = WorkoutStore(str(tmp_path / "workouts.sqlite3"))
    hulk = HulkAgent(
        groq_client=groq_client,
        workout_store=store,
        tool_registry=FakeHulkTools(),
    )

    reply = await hulk.respond(
        "Log bench press 80kg for 5 reps, 3 sets",
        user_id="user-1",
    )

    assert reply == "Hulk final"
    user_message = groq_client.calls[0][1].content
    assert "Saved workout log" in user_message
    assert "Recent workout history" in user_message
    assert "bench" in user_message
    assert "80kg" in user_message


async def test_hulk_uses_food_lookup_tool(tmp_path):
    groq_client = FakeGroqClient()
    tools = FakeHulkTools()
    hulk = HulkAgent(
        groq_client=groq_client,
        workout_store=WorkoutStore(str(tmp_path / "workouts.sqlite3")),
        tool_registry=tools,
    )

    await hulk.respond("7-11 雞肉飯 熱量 macros?", user_id="user-1")

    assert tools.food_queries == ["7-11 雞肉飯 熱量 macros?"]
    user_message = groq_client.calls[0][1].content
    assert "get_taiwan_food_info" in user_message
    assert "Food lookup context" in user_message


async def test_hulk_uses_research_lookup_tool(tmp_path):
    groq_client = FakeGroqClient()
    tools = FakeHulkTools()
    hulk = HulkAgent(
        groq_client=groq_client,
        workout_store=WorkoutStore(str(tmp_path / "workouts.sqlite3")),
        tool_registry=tools,
    )

    await hulk.respond("What does research say about rest time?", user_id="user-1")

    assert tools.research_queries == ["What does research say about rest time?"]
    user_message = groq_client.calls[0][1].content
    assert "get_scientific_workout_research" in user_message
    assert "Research context" in user_message


async def test_hulk_saves_workout_plan_context(tmp_path):
    groq_client = FakeGroqClient()
    plan_store = WorkoutPlanStore(str(tmp_path / "plans.sqlite3"))
    hulk = HulkAgent(
        groq_client=groq_client,
        workout_store=WorkoutStore(str(tmp_path / "workouts.sqlite3")),
        plan_store=plan_store,
        tool_registry=FakeHulkTools(),
    )

    await hulk.respond("Build me a 4-day workout plan for hypertrophy", "user-1")

    latest = plan_store.latest_plan("user-1")
    assert latest is not None
    assert latest.plan.days_per_week == 4
    user_message = groq_client.calls[0][1].content
    assert "Saved workout plan" in user_message
    assert "Chest press" in user_message


async def test_hulk_injects_latest_plan_when_not_creating_new_one(tmp_path):
    groq_client = FakeGroqClient()
    plan_store = WorkoutPlanStore(str(tmp_path / "plans.sqlite3"))
    hulk = HulkAgent(
        groq_client=groq_client,
        workout_store=WorkoutStore(str(tmp_path / "workouts.sqlite3")),
        plan_store=plan_store,
        tool_registry=FakeHulkTools(),
    )

    await hulk.respond("Build me a 3-day workout plan for strength", "user-1")
    await hulk.respond("What should I train today?", "user-1")

    user_message = groq_client.calls[1][1].content
    assert "Latest saved workout plan" in user_message
    assert "3-Day Strength Training Plan" in user_message


async def test_hulk_analyzes_physique_photo(tmp_path):
    from app.media.models import MediaAttachment

    analyzer = FakePhysiqueAnalyzer()
    hulk = HulkAgent(
        groq_client=FakeGroqClient(),
        physique_analyzer=analyzer,
    )
    attachment = MediaAttachment(
        path=tmp_path / "photo.jpg",
        mime_type="image/jpeg",
        source="test",
    )

    result = await hulk.analyze_physique_photo(attachment, context="front photo")

    assert result == "Physique analysis"
    assert analyzer.calls == [(attachment, "front photo")]


async def test_hulk_analyzes_food_or_general_image(tmp_path):
    from app.media.models import MediaAttachment

    analyzer = FakeImageAnalyzer()
    hulk = HulkAgent(
        groq_client=FakeGroqClient(),
        image_analyzer=analyzer,
    )
    attachment = MediaAttachment(
        path=tmp_path / "meal.jpg",
        mime_type="image/jpeg",
        source="test",
    )

    result = await hulk.analyze_image(attachment, context="food photo")

    assert "Food check:" in result
    assert "Please confirm:" in result
    assert analyzer.calls == [(attachment, "food photo")]
