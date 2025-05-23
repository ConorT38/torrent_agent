from datetime import datetime, timedelta

class CacheEntry:
    def __init__(self, data):
        self.data = data
        self.expiry_time = datetime.now() + timedelta(minutes=10)

    def is_expired(self):
        return datetime.now() > self.expiry_time