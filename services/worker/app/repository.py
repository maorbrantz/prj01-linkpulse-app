class StatsRepository:
    def __init__(self, table):
        self._table = table

    def increment(self, short_code: str, day: str, amount: int) -> None:
        self._table.update_item(
            Key={"short_code": short_code, "day": day},
            UpdateExpression="ADD #count :amount",
            ExpressionAttributeNames={"#count": "count"},
            ExpressionAttributeValues={":amount": amount},
        )
