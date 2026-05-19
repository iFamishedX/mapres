class Layer:
    def __init__(self, name, maps=None):
        self.name = name
        self.maps = maps or []

    def add(self, m):
        self.maps.append(m)

    def __iter__(self):
        return iter(self.maps)
