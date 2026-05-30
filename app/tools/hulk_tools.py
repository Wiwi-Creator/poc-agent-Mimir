from app.tools.models import ToolResult
from app.tools.web_search import WebSearchTool


class HulkToolRegistry:
    def __init__(self, search_tool: WebSearchTool | None = None) -> None:
        self.search_tool = search_tool or WebSearchTool()

    async def get_taiwan_food_info(self, food_name: str) -> ToolResult:
        query = (
            f"{food_name} 營養 熱量 蛋白質 碳水 脂肪 "
            "site:tw OR site:com.tw OR site:ptt.cc OR site:dcard.tw"
        )
        return await self.search_tool.search(
            query=query,
            name="get_taiwan_food_info",
        )

    async def get_scientific_workout_research(self, workout_topic: str) -> ToolResult:
        query = (
            f"{workout_topic} "
            "site:pubmed.ncbi.nlm.nih.gov OR site:strongerbyscience.com "
            "OR site:strengthandconditioningresearch.com"
        )
        return await self.search_tool.search(
            query=query,
            name="get_scientific_workout_research",
        )
