import asyncio
import os
from collections import defaultdict

from vase import Vase
from vase.response import HttpResponse
import ujson as json

from .simple_json_rpc import SimpleJsonRpc
from .subscriptions_service import subscriptions_service

def create_app(state, scheduler):
    app = Vase(__name__)

    def _jsonify(obj={}):
        return HttpResponse(json.dumps(obj), content_type="application/json")

    def _broadcast_status(building=None):
        buildings = state.buildings
        if building:
            buildings = filter(lambda s: s.name == building, buildings)
        message = json.dumps({'status': state.__dict__()})
        BuildingsStatusEndpoint.broadcast(message, building=building)

    #
    # Static files
    #
    @app.route(path="/", methods=("GET"))
    def root(request):
        body = open(os.path.join(os.path.dirname(__file__), 'static', 'index.html'), 'r', encoding='utf-8').read()
        return HttpResponse(body, content_type="text/html")

    @app.route(path="/html/{fname}", methods=("GET"))
    def html(request, fname):
        body = open(os.path.join(os.path.dirname(__file__), 'static/html', fname), 'r', encoding='utf-8').read()
        return HttpResponse(body, content_type="text/html")

    @app.route(path="/js/{fname}", methods=("GET"))
    def js(request, fname):
        body = open(os.path.join(os.path.dirname(__file__), 'static/js', fname), 'r', encoding='utf-8').read()
        return HttpResponse(body, content_type="application/javascript")

    @app.route(path="/css/{fname}", methods=("GET"))
    def css(request, fname):
        body = open(os.path.join(os.path.dirname(__file__), 'static/css', fname), 'r', encoding='utf-8').read()
        return HttpResponse(body, content_type="text/css")

    #
    # The resource buildings
    #
    @app.route(path="/api/v1/buildings/{building}/cars/{car:\d+}/buttons/{floor:\d+}", methods="POST")
    def car_buttons_floor(request, building, car: int, floor: int):
        car   = int(car)
        floor = int(floor)
        print("Send the car {} to the floor {}".format(car, floor))
        state.cars_buttons_call(building, car, floor)
        scheduler.schedule_car(building, car)
        _broadcast_status(building=building)
        return _jsonify()

    @app.route(path="/api/v1/buildings/{building}/cars/{car}/buttons/toggle", methods="POST")
    def car_buttons_stop(request, building, car: int):
        car   = int(car)
        print("Stop the car {}".format(car))
        state.cars_buttons_toggle(building, car)
        scheduler.schedule_car(building, car)
        _broadcast_status(building=building)
        return _jsonify()

    @app.route(path="/api/v1/buildings/{building}/floors/{floor:\d+}/buttons/call", methods="POST")
    def floors_buttons_call(request, building, floor: int):
        floor = int(floor)
        print("Call the Nearest Car on the floor {}".format(floor))
        scheduler.call_car(building, floor)
        _broadcast_status(building=building)
        return _jsonify()

    @app.route(path="/api/v1/buildings", methods="POST")
    def buildings_post(request):
        data     = json.loads((yield from request.body.read()).decode('utf-8'))
        name     = str(data['name'])
        n_cars   = int(data['n_cars'])
        n_floors = int(data['n_floors'])
        speed    = float(data['speed'])
        print("Create a building \"{}\" with {} floors and {} cars.".format(name, n_floors, n_cars))
        state.create_building(name, n_floors, n_cars, speed)
        _broadcast_status()
        return _jsonify()

    @app.route(path="/api/v1/buildings/{building}", methods="DELETE")
    def buildings_delete(request, building):
        print("Destroy the building \"{}\".".format(building))
        state.destroy_building(building)
        _broadcast_status()
        return _jsonify()

    @app.route(path="/api/v1/buildings/{building}/status", methods="GET")
    def buildings_status(request, building):
        return _jsonify({'status': state.buildings[building].__dict__()})

    @app.route(path="/api/v1/status", methods="GET")
    def status(request):
        return _jsonify({'status': state.__dict__()})

    #
    # WebSockets endpoint
    #
    app.endpoint(path="/ws", with_sockjs=False)(BuildingsStatusEndpoint)

    subscriptions_service.on_tick(_broadcast_status)

    return app


class BuildingsStatusEndpoint:
    """
    WebSocket endpoint
    Has the following attributes:
    `bag` - a dictionary that is shared between all instances of this endpoint
    `transport` - used to send messages into the websocket, has send(message), close() methods
    """

    @classmethod
    def broadcast(cls, message, building=None):
        subscriptions = subscriptions_service.values()
        if building:
            subscriptions = filter(lambda s: s.building == building if s.building else True, subscriptions)
        for s in subscriptions:
            s.client.transport.send(message)

    def on_connect(self):
        pass

    def on_message(self, message):
        request = SimpleJsonRpc(message)
        if request.method == 'subscribe':
            self._subscribe(**request.params)
        elif request.method == 'get_status':
            self._get_status(**request.params)

    def on_close(self, exc=None):
        subscriptions_service.remove_subscription(self)

    def _subscribe(self, building=None):
        subscriptions_service.add_subscription(self, building=building)

    def _get_status(self):
        self.transport.send(json.dumps({'status': state.__dict__()}))
