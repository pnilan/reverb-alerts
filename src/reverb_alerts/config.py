from pathlib import Path

import yaml
from pydantic import BaseModel

from reverb_alerts.models import ReverbCondition


class Watch(BaseModel):
    name: str
    query: str
    max_price: float
    include_shipping: bool = False
    location: str | None = None
    conditions: list[ReverbCondition] | None = None


class WatchConfig(BaseModel):
    watches: list[Watch]


def load_watches(config_path: Path) -> list[Watch]:
    with open(config_path) as f:
        data = yaml.safe_load(f)

    config = WatchConfig(**data)
    return config.watches
