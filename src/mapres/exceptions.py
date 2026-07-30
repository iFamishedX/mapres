class MapResError(Exception):
    pass

class MissingKeyError(MapResError):
    def __init__(self, key):
        super().__init__(f'Missing key {key!r}')
        self.key = key

class MapSyntaxError(MapResError):
    pass
