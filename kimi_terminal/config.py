from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class WatchlistItem:
    code: str
    name: str
    hold_cost: float | None = None
    hold_quantity: int | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"code": self.code, "name": self.name}
        if self.hold_cost is not None:
            d["hold_cost"] = self.hold_cost
        if self.hold_quantity is not None:
            d["hold_quantity"] = self.hold_quantity
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "WatchlistItem":
        return cls(
            code=str(d["code"]),
            name=str(d["name"]),
            hold_cost=float(d["hold_cost"]) if "hold_cost" in d else None,
            hold_quantity=int(d["hold_quantity"]) if "hold_quantity" in d else None,
        )


@dataclass
class AppConfig:
    theme: str = "dark"
    refresh_interval_seconds: int = 30
    price_precision: int = 2
    cache_db_path: str = "~/.cache/kimi-terminal/cache.db"

    def resolved_cache_path(self) -> Path:
        return Path(os.path.expanduser(self.cache_db_path))

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "AppConfig":
        return cls(
            theme=str(d.get("theme", "dark")),
            refresh_interval_seconds=int(d.get("refresh_interval_seconds", 30)),
            price_precision=int(d.get("price_precision", 2)),
            cache_db_path=str(d.get("cache_db_path", "~/.cache/kimi-terminal/cache.db")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "theme": self.theme,
            "refresh_interval_seconds": self.refresh_interval_seconds,
            "price_precision": self.price_precision,
            "cache_db_path": self.cache_db_path,
        }


class ConfigManager:
    def __init__(self, config_dir: Path | None = None) -> None:
        self.config_dir = config_dir or Path.home() / ".config" / "kimi-terminal"
        self.config_file = self.config_dir / "config.yaml"
        self.watchlist_file = self.config_dir / "watchlist.yaml"

    def ensure_directories(self) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        cache_dir = Path.home() / ".cache" / "kimi-terminal"
        cache_dir.mkdir(parents=True, exist_ok=True)

    def load_config(self) -> AppConfig:
        if not self.config_file.exists():
            return AppConfig()
        with open(self.config_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return AppConfig.from_dict(data)

    def save_config(self, config: AppConfig) -> None:
        self.ensure_directories()
        with open(self.config_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(config.to_dict(), f, allow_unicode=True, sort_keys=False)

    def load_watchlist(self) -> list[WatchlistItem]:
        if not self.watchlist_file.exists():
            default = [
                WatchlistItem(code="600519.SH", name="贵州茅台"),
                WatchlistItem(code="0700.HK", name="腾讯控股"),
            ]
            self.save_watchlist(default)
            return default
        with open(self.watchlist_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        items = data.get("watchlist", []) if isinstance(data, dict) else []
        return [WatchlistItem.from_dict(i) for i in items]

    def save_watchlist(self, items: list[WatchlistItem]) -> None:
        self.ensure_directories()
        with open(self.watchlist_file, "w", encoding="utf-8") as f:
            yaml.safe_dump({"watchlist": [i.to_dict() for i in items]}, f, allow_unicode=True, sort_keys=False)

    def add_to_watchlist(self, item: WatchlistItem) -> list[WatchlistItem]:
        items = self.load_watchlist()
        codes = {i.code.upper() for i in items}
        if item.code.upper() in codes:
            return items
        items.append(item)
        self.save_watchlist(items)
        return items

    def remove_from_watchlist(self, code: str) -> list[WatchlistItem]:
        items = self.load_watchlist()
        items = [i for i in items if i.code.upper() != code.upper()]
        self.save_watchlist(items)
        return items
