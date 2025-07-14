from dataclasses import asdict, dataclass
from datetime import datetime

@dataclass
class Image:
    file_name: str
    cdn_path: str
    uploaded: datetime

    def to_dict(self):
        return asdict(self)