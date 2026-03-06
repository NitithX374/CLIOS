# models.py

class Interface:
    def __init__(self, name):
        self.name = name
        self.ip = None
        self.connected_to = None


class Router:
    def __init__(self, name):
        self.name = name
        self.interfaces = {}
        self.ospf_enabled = False
        self.ospf_neighbors = {}

    def add_interface(self, if_name):
        if if_name not in self.interfaces:
            self.interfaces[if_name] = Interface(if_name)


class Network:
    def __init__(self):
        self.routers = {}

    def add_router(self, name):
        if name not in self.routers:
            self.routers[name] = Router(name)

    def connect(self, r1, i1, r2, i2):

        self.routers[r1].add_interface(i1)
        self.routers[r2].add_interface(i2)

        self.routers[r1].interfaces[i1].connected_to = (r2, i2)
        self.routers[r2].interfaces[i2].connected_to = (r1, i1)