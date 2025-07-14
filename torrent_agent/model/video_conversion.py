from dataclasses import dataclass, asdict

@dataclass
class VideoConversion:
    id: int = None
    original_video_id: int = None
    original_filename: str = None
    converted_filename: str = None
    conversion_status: str = "pending"
    error_message: str = None
    created_at: str = None
    updated_at: str = None

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(data: dict):
        return VideoConversion(**data)