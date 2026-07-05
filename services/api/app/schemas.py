from pydantic import BaseModel, HttpUrl


class CreateLinkRequest(BaseModel):
    url: HttpUrl


class CreateLinkResponse(BaseModel):
    short_code: str
    short_url: str


class DailyCount(BaseModel):
    day: str
    count: int


class StatsResponse(BaseModel):
    short_code: str
    total_clicks: int
    daily: list[DailyCount]
