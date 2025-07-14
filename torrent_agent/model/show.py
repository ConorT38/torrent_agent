from dataclasses import asdict, dataclass

@dataclass
class Show:
    name: str
    description: str
    thumbnail_id: int
    show_folder: str
    id: int | None = None

    def to_dict(self):
        return asdict(self)

@dataclass
class Season:
    show_id: int
    season_number: int
    id: int | None = None

    def to_dict(self):
        return asdict(self)

@dataclass
class Episode:
    video_id: int
    episode_number: int
    show_id: int
    description: str
    season_id: int | None = None

    def to_dict(self):
        return asdict(self)