from dataclasses import asdict, dataclass
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

    def to_dict(self):
        data = asdict(self)
        data['uploaded'] = self.uploaded.isoformat() if self.uploaded else None
        return data
    
    @classmethod
    def from_dict(cls, data):
        data['uploaded'] = datetime.fromisoformat(data['uploaded']) if data.get('uploaded') else None
        return cls(**data)