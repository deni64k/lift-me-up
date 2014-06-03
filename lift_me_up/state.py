import os.path
import pickle

import jsonpickle

from .models import Building


class State(object):
    def __init__(self):
        self.buildings = dict()
    
    def seed(self):
        self.create_building('mitino-house', 24, 3, 1.0)
    
    def create_building(self, name, n_floors, n_cars, speed):
        if not name in self.buildings:
            self.buildings[name] = Building(name, n_floors, n_cars, speed)

    def destroy_building(self, name):
        del self.buildings[name]
    
    def cars_buttons_call(self, name, car, floor):
        self.buildings[name].cars_buttons_call(car, floor)

    def cars_buttons_toggle(self, name, car):
        self.buildings[name].cars_buttons_toggle(car)
    
    def tick(self):
        for building in self.buildings.values():
            building.tick()
        self.save()
    
    def __dict__(self):
        return {'buildings': self.buildings}

    def __getstate__(self):
        return {'buildings': self.buildings}
    
    def __setstate__(self, state):
        self.buildings = state['buildings']

    fname = 'state.pickle'
    @classmethod
    def load(cls):
        with open(cls.fname, 'rb') as f:
            return pickle.loads(f.read())
        
    def save(self):
        with open(self.__class__.fname, 'wb') as f:
            f.write(pickle.dumps(self))

def state_factory():
    if os.path.isfile(State.fname):
        try:
            return State.load()
        except ValueError:
            pass
    return State()

state = state_factory()
state.seed()
