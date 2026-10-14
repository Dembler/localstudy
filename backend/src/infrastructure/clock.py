from datetime import UTC, date, datetime


class SystemClock:
    def today(self) -> date:
        return date.today()

    def now(self) -> datetime:
        return datetime.now(UTC).replace(tzinfo=None)
