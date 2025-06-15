from dataclasses import dataclass
from datetime import datetime

@dataclass
class Video:
    id: int = None
    file_name: str
    cdn_path: str
    title: str
    uploaded: datetime
    entertainment_type: str
    thumbnail_id: int = None