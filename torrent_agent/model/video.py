from dataclasses import dataclass
from datetime import datetime

@dataclass
class Video:
    file_name: str
    cdn_path: str
    title: str
    uploaded: datetime
    entertainment_type: str
    id: int = None
    thumbnail_id: int = None