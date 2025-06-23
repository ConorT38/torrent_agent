from datetime import datetime, timedelta

CACHE_TTL_MINUTES = 90

class CacheEntry:
    def __init__(self, data):
        self.data = data
        self.expiry_time = datetime.now() + timedelta(minutes=CACHE_TTL_MINUTES)

    def is_expired(self):
        return datetime.now() > self.expiry_time