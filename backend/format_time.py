def format_timestamp(seconds: int | float | None) -> str:
    total = max(0, int(seconds or 0))
    minutes, secs = divmod(total, 60)
    return f"{minutes}-{secs:02d}"


def parse_timestamp(value: str | int | float | None) -> int:
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return max(0, int(value))
    text = str(value).strip()
    if not text:
        return 0
    if text.isdigit():
        return int(text)
    if "-" in text:
        minutes_text, seconds_text = text.split("-", 1)
        return max(0, int(minutes_text) * 60 + int(seconds_text))
    raise ValueError(f"unsupported time format: {value!r}")
