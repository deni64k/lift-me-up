import asyncio
import math

from .constants import *
from .models import CarDirection
from .subscriptions_service import subscriptions_service


class Scheduler(object):
    def __init__(self, state):
        self._state = state

    def run(self, loop=None):
        if not loop:
            loop = asyncio.get_event_loop()
        loop.call_later(SCHEDULER_QUANTUM, self._schedule_cars)

    def _schedule_cars(self):
        self._tick()
        subscriptions_service.tick()

        loop = asyncio.get_event_loop()
        loop.call_later(SCHEDULER_QUANTUM, self._schedule_cars)

    def _tick(self):
        for building in self._state.buildings.values():
            self._tick_building(building)
        self._state.save()

    def _tick_building(self, building):
        for car in building.cars:
            self._tick_car(building, car)

    def _tick_car(self, building, car):
        if car.is_moving():
            car.floor += car.direction.value * car.speed * SCHEDULER_QUANTUM
        if car.is_arrived():
            car.floor  = car.floor_approximated
            car.backlog.append(car.floor)
            car.destinations.remove(car.floor)
            self._schedule_car(car)
            building.floors[car.floor] = 0

    def _find_nearest_car(self, building, floor):
        dists = sorted(self._car_distances(building, floor), key=lambda cs: cs[1], reverse=False)
        return dists[0][0]

    def _car_distances(self, building, floor):
        for car in building.standby_cars():
            yield (car, self._car_distance(car, floor))

    def _car_distance(self, car, floor):
        # Если лифт стоит или движется в сторону вызова.
        if not car.direction or \
                math.copysign(1, floor - car.floor_approximated) == car.direction.value:
            return math.fabs(car.floor_approximated - floor)
        # Если лифт движется в противоположную сторону от вызова.
        elif math.copysign(1, floor - car.floor_approximated) == -car.direction.value:
            return math.fabs(car.floor_approximated - floor) + 2 * math.fabs(max(car.destinations) - floor)
        # Что-то поломалось в логике.
        else:
            raise NotImplementedError

    def call_car(self, building, floor):
        building = self._state.buildings[building]
        car = self._find_nearest_car(building, floor)
        if car and car.floor_approximated != floor:
            building.floors[floor] += 1
            car.send_to_floor(floor)
        self._schedule_car(car)

    def schedule_car(self, building, car):
        building = self._state.buildings[building]
        car = building.cars[car]
        self._schedule_car(car)

    def _schedule_car(self, car):
        if not car.destinations:
            car.direction = None
        elif any(map(lambda f: f > car.floor, car.destinations)):
            car.direction = CarDirection.up
        else:
            car.direction = CarDirection.down
