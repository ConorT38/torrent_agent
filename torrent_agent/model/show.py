from dataclasses import asdict, dataclass

@dataclass
class Show:
    name: str
    description: str
    thumbnail_id: int
    id: int = None

    def to_dict(self):
        return asdict(self)

@dataclass
class Season:
    show_id: int
    season_number: int
    id: int = None

    def to_dict(self):
        return asdict(self)

@dataclass
class Episode:
    video_id: int
    episode_number: int
    show_id: int
    season_id: int = None

    def to_dict(self):
        return asdict(self)