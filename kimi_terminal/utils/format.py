from __future__ import annotations


def fmt_price(value: float | None, precision: int = 2) -> str:
    if value is None:
        return "-"
    return f"{value:,.{precision}f}"


def fmt_change(value: float | None) -> str:
    if value is None:
        return "-"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:,.2f}"


def fmt_pct(value: float | None) -> str:
    if value is None:
        return "-"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:,.2f}%"


def fmt_volume(value: float | None) -> str:
    if value is None:
        return "-"
    if value >= 1_0000_0000:
        return f"{value / 1_0000_0000:.2f}亿"
    if value >= 1_0000:
        return f"{value / 1_0000:.2f}万"
    return f"{value:,.0f}"


def color_for_change(value: float | None) -> str:
    # Chinese market convention: red = up, green = down
    if value is None:
        return "white"
    if value > 0:
        return "red"
    if value < 0:
        return "green"
    return "white"
