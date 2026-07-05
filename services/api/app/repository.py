from datetime import datetime, timezone

from botocore.exceptions import ClientError


class LinkRepository:
    def __init__(self, table):
        self._table = table

    def save(self, short_code: str, url: str) -> None:
        self._table.put_item(
            Item={
                "short_code": short_code,
                "url": url,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            ConditionExpression="attribute_not_exists(short_code)",
        )

    def get(self, short_code: str) -> dict | None:
        response = self._table.get_item(Key={"short_code": short_code})
        return response.get("Item")

    def exists(self, short_code: str) -> bool:
        return self.get(short_code) is not None


class StatsRepository:
    def __init__(self, table):
        self._table = table

    def by_short_code(self, short_code: str) -> list[dict]:
        try:
            response = self._table.query(
                KeyConditionExpression="short_code = :sc",
                ExpressionAttributeValues={":sc": short_code},
            )
        except ClientError:
            return []
        return response.get("Items", [])
