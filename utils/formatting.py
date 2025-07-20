from __future__ import annotations


def short_number(value: int | float) -> str:
    value = int(value)
    if value >= 1_000_000:
        # e.g. 1500000 -> 1.5кк
        if value % 1_000_000 == 0:
            return f"{value // 1_000_000}k"
        else:
            return f"{value / 1_000_000:.1f}k"
    elif value >= 1000:
        if value % 1000 == 0:
            return f"{value // 1000}"
        else:
            return f"{value / 1000:.1f}k"
    else:
        return str(value)
