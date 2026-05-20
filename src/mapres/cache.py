class LRUCache:
    def __init__(self, max_size: int = 1024):
        self.max_size = max_size
        self.data = {}

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value):
        if len(self.data) >= self.max_size:
            self.data.pop(next(iter(self.data)))
        self.data[key] = value
