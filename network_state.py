class Interface:

    def __init__(self, name):
        self.name = name
        self.ip = None
        self.link = None
        self.area = None
        self.cost = 10

class Router:

    def __init__(self, name):
        self.name = name
        self.interfaces = {}
        self.ospf_enabled = False
        self.external_domain = None


class Network:

    def __init__(self):
        self.routers = {}
        self.area_types = {}

    def add_router(self, name):

        if name not in self.routers:
            self.routers[name] = Router(name)

    def add_interface(self, router_name, intf_name):

        router = self.routers.get(router_name)

        if not router:
            return "Router not found"

        if intf_name not in router.interfaces:
            router.interfaces[intf_name] = Interface(intf_name)

    def set_ip(self, router_name, intf_name, ip):

        router = self.routers.get(router_name)

        if not router:
            return "Router not found"

        intf = router.interfaces.get(intf_name)

        if not intf:
            return "Interface not found"

        intf.ip = ip

    def set_cost(self, router_name, intf_name, cost):

        router = self.routers.get(router_name)

        if not router:
            return "Router not found"

        intf = router.interfaces.get(intf_name)

        if not intf:
            return "Interface not found"

        try:
            intf.cost = int(cost)
        except ValueError:
            return "Cost must be an integer"

    def connect(self, r1, i1, r2, i2):

        router1 = self.routers.get(r1)
        router2 = self.routers.get(r2)

        if not router1 or not router2:
            return "Router not found"

        intf1 = router1.interfaces.get(i1)
        intf2 = router2.interfaces.get(i2)

        if not intf1 or not intf2:
            return "Interface not found"

        intf1.link = f"{r2}:{i2}"
        intf2.link = f"{r1}:{i1}"

    def enable_ospf(self, router):

        r = self.routers.get(router)

        if not r:
            return "Router not found"

        r.ospf_enabled = True


network = Network()