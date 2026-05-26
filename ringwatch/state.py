from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json

from .models import NewsItem


@dataclass
class SeenState:
    path: Path
    seen: dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls, path: str | Path) -> "SeenState":
        state_path = Path(path)
        if not state_path.exists():
            return cls(path=state_path)
        with state_path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
        seen = raw.get("seen", {})
        if not isinstance(seen, dict):
            seen = {}
        return cls(path=state_path, seen={str(k): str(v) for k, v in seen.items()})

    def is_seen(self, item: NewsItem) -> bool:
        return item.key in self.seen

    def mark(self, items: list[NewsItem]) -> None:
        now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        for item in items:
            self.seen[item.key] = now

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"seen": self.seen}
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
