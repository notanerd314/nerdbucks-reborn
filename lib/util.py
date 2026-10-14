def pretty_time(seconds: int | float) -> str:
    """Formats time pretty and cute"""
    seconds = int(seconds)

    if seconds < 0:
        raise ValueError("seconds cannot be negative")

    units = [
        ("year", 31_536_000),
        ("day", 86_400),
        ("hour", 3_600),
        ("minute", 60),
        ("second", 1),
    ]

    parts = []

    for name, size in units:
        amount, seconds = divmod(seconds, size)

        if amount:
            label = name if amount == 1 else f"{name}s"
            parts.append(f"{amount} {label}")

    return ", ".join(parts) if parts else "0 seconds"