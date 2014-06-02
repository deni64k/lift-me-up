from array import array
from collections import deque
from enum import Enum
import math

from . import constants


class CarDirection(Enum):
    down    = -1
    up      = 1


class CarStatus(Enum):
    stopped = 0
    standby = 1
    


class Car(object):
    def __init__(self, floors, floor=0.0, speed=1.0, capability=250):
        self.backlog      = deque(maxlen=floors)
        self.capability   = capability
        self.destinations = set()
        self.direction    = None
        self.floor        = floor
        self.speed        = speed
        self.status       = CarStatus.standby
    
    def __dict__(self):
        return {
            'backlog':      list(self.backlog),
            'capability':   self.capability,
            'destinations': self.destinations,
            'direction':    self.direction.name if self.direction else None,
            'floor':        self.floor,
            'floor_approximated': self.floor_approximated(),
            'speed':        self.speed,
            'status':       self.status.name,
        }
    
    def __getstate__(self):
        return {
            'backlog':      self.backlog,
            'capability':   self.capability,
            'destinations': self.destinations,
            'direction':    self.direction,
            'floor':        self.floor,
            'speed':        self.speed,
            'status':       self.status,
        }

    def __setstate__(self, state):
        self.backlog      = state['backlog']
        self.capability   = state['capability']
        self.destinations = state['destinations']
        self.direction    = state['direction']
        self.floor        = state['floor']
        self.speed        = state['speed']
        self.status       = state['status']
    
    def floor_approximated(self):
        eps = self.speed * constants.SCHEDULER_QUANTUM / 2.0
        if not self.direction:
            return math.floor(self.floor)
        elif self.direction == CarDirection.down:
            if math.fabs(math.floor(self.floor) - self.floor) <= eps:
                return math.floor(self.floor)
            else:
                return math.ceil(self.floor)
        elif self.direction == CarDirection.up:
            if math.fabs(math.ceil(self.floor) - self.floor) <= eps:
                return math.ceil(self.floor)
            else:
                return math.floor(self.floor)
    
    def toggle(self):
        self.status = CarStatus.standby if self.status == CarStatus.stopped else CarStatus.stopped
        self.schedule_direction()

    def tick(self, building):
        if self.is_moving():
            self.floor += self.direction.value * self.speed * constants.SCHEDULER_QUANTUM
        if self.is_arrived():
            self.floor  = self.floor_approximated()
            self.backlog.append(self.floor)
            self.destinations.remove(self.floor)
            self.schedule_direction()
            building.on_arrived(self)
    
    def is_moving(self):
        return self.status == CarStatus.standby and \
               self.direction and self.floor_approximated() not in self.destinations

    def is_arrived(self):
        return self.direction and self.floor_approximated() in self.destinations

    def schedule_direction(self):
        if not self.destinations:
            self.direction = None
        elif any(map(lambda f: f > self.floor, self.destinations)):
            self.direction = CarDirection.up
        else:
            self.direction = CarDirection.down

    def send_to_floor(self, floor):
        if not self.floor_approximated() == floor:
            self.destinations.add(floor)
            self.schedule_direction()


class Building(object):
    def __init__(self, name, n_floors, n_cars, speed):
        self.name     = name
        self.n_floors = n_floors
        self.floors   = array('i', (False for i in range(n_floors)))
        self.n_cars   = n_cars
        self.cars     = list(Car(self.n_floors, floor=i * self.n_floors / self.n_cars, speed=speed) for i in range(n_cars))

    def standby_cars(self):
        return (yield from filter(lambda c: c.status == CarStatus.standby, self.cars))

    def schedule(self):
        pass

    def tick(self):
        for car in self.cars:
            car.tick(self)
    
    def on_arrived(self, car):
        self.floors[car.floor] = 0

    def __dict__(self):
        return {
            'name':     self.name,
            'n_floors': self.n_floors,
            'floors':   self.floors.tolist(),
            'n_cars':   self.n_cars,
            'cars':     list(c.__dict__() for c in self.cars),
        }

    def __getstate__(self):
        return {
            'name':     self.name,
            'n_floors': self.n_floors,
            'floors':   self.floors,
            'n_cars':   self.n_cars,
            'cars':     self.cars,
        }

    def __setstate__(self, state):
        self.name     = state['name']
        self.n_floors = state['n_floors']
        self.floors   = state['floors']
        self.n_cars   = state['n_cars']
        self.cars     = state['cars']
    
    def cars_buttons_call(self, car, floor):
        self.cars[car].send_to_floor(floor)

    def cars_buttons_toggle(self, car):
        self.cars[car].toggle()

    def floors_buttons_call(self, floor):
        car = self.find_nearest_car(floor)
        if car and car.floor_approximated() != floor:
            self.floors[floor] += 1
            car.send_to_floor(floor)
    
    def find_nearest_car(self, floor):
        print(list(self._nearest_car_scores(floor)))
        scores = sorted(self._nearest_car_scores(floor), key=lambda cs: cs[1], reverse=False)
        return scores[0][0]
    
    def _nearest_car_scores(self, floor):
        for car in self.standby_cars():
            yield (car, self._nearest_car_score(car, floor))

    def _nearest_car_score(self, car, floor):
        # Если лифт стоит или движется в сторону вызова.
        if not car.direction or \
                math.copysign(1, floor - car.floor_approximated()) == car.direction.value:
            return math.fabs(car.floor_approximated() - floor)
        # Если лифт движется в противоположную сторону от вызова.
        elif math.copysign(1, floor - car.floor_approximated()) == -car.direction.value:
            return math.fabs(car.floor_approximated() - floor) + 2 * math.fabs(max(car.destinations) - floor)
        # Что-то поломалось в логике.
        else:
            raise NotImplementedError
