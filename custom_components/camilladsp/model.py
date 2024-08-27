from dataclasses import dataclass


@dataclass
class CDSPData:

    state: str
    volume: float
    mute: bool
    source: str
    source_list: list[str]
