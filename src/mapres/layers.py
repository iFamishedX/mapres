class Layer:
    '''Holds a map with a priority'''
    def __init__(self, name, maps=None, priority=0):
        self.name = name
        self.maps = maps or []
        self.priority = priority

    def add(self, m):
        self.maps.append(m)

    def __iter__(self):
        return iter(self.maps)


class LayerStack:
    '''Manages ordered layers'''
    def __init__(self, layers=None):
        self.layers = {}
        if layers:
            for layer in layers:
                self.layers[layer.name] = layer

    def add_layer(self, layer):
        self.layers[layer.name] = layer

    def remove_layer(self, name):
        if name in self.layers:
            del self.layers[name]

    def get_layer(self, name):
        return self.layers.get(name)

    def clone(self):
        return LayerStack(list(self.layers.values()))

    def all_maps(self):
        ordered = sorted(self.layers.values(), key=lambda l: l.priority)
        for layer in ordered:
            for m in layer:
                yield m

    def __iter__(self):
        return self.all_maps()
