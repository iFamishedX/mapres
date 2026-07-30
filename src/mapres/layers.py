# layers.py

class Layer:
    """
    A single layer containing one or more maps.
    Priority determines resolution order.
    Lower priority = earlier lookup.
    """
    def __init__(self, maps=None, priority=0):
        self.maps = maps or []
        self.priority = priority

    def add(self, m):
        self.maps.append(m)

    def __iter__(self):
        return iter(self.maps)


class LayerStack:
    """
    A simple ordered list of layers.
    No names, no dicts, no complexity.
    Just priority-sorted layers.
    """
    def __init__(self):
        self.layers = []  # list of Layer objects

    def add_layer(self, maps, priority=0):
        """
        Add a new layer containing one or more maps.
        maps: datamap instance, datamap class, or dict
        priority: lower = earlier lookup
        """
        layer = Layer(
            maps=[maps] if not isinstance(maps, list) else maps,
            priority=priority
        )
        self.layers.append(layer)
        self.layers.sort(key=lambda l: l.priority)

    def all_maps(self):
        """
        Yield all maps in priority order.
        """
        for layer in self.layers:
            for m in layer:
                yield m

    def clone(self):
        """
        Return a shallow copy of the layerstack.
        """
        new = LayerStack()
        new.layers = list(self.layers)
        return new
