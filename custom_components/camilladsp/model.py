from dataclasses import dataclass


@dataclass
class CDSPData:

    state: str
    volume: float
    volume_fader: dict[str, float]
    mute: bool
    is_fader_muted: dict[str, bool]
    source: str
    source_list: list[str]
    capturerate: int
