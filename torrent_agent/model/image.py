from dataclasses import dataclass
from datetime import datetime

@dataclass
class Image:
    file_name: str
    cdn_path: str
    uploaded: datetime
