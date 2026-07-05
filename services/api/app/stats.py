from .schemas import DailyCount, StatsResponse


def build_stats(short_code: str, items: list[dict]) -> StatsResponse:
    daily = [
        DailyCount(day=item["day"], count=int(item["count"]))
        for item in sorted(items, key=lambda i: i["day"])
    ]
    total = sum(entry.count for entry in daily)
    return StatsResponse(short_code=short_code, total_clicks=total, daily=daily)
