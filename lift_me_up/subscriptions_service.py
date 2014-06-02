from lift_me_up.state import state

class Subscription(object):
    def __init__(self, client, building=None):
        self._client   = client
        self._building = building

    @property
    def client(self):
        return self._client

    @property
    def building(self):
        return self._building

class SubscriptionsService(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._callbacks = list()

    def add_subscription(self, client, building=None):
        self[client] = Subscription(client, building=building)

    def remove_subscription(self, client):
        del self[client]

    def on_tick(self, callback):
        self._callbacks.append(callback)

    def tick(self):
        for c in self._callbacks:
            c(self)
        
    @property
    def subscriptions(self):
        return self
    

subscriptions_service = SubscriptionsService()
