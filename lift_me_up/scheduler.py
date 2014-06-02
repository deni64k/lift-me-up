import asyncio

from .constants import *
from .subscriptions_service import subscriptions_service


class Scheduler(object):
    def __init__(self, state):
        self._state = state

    def run(self, loop=None):
        if not loop:
            loop = asyncio.get_event_loop()
        loop.call_later(SCHEDULER_QUANTUM, self._schedule_cars)

    def _schedule_cars(self):
        self._state.tick()
        subscriptions_service.tick()

        loop = asyncio.get_event_loop()
        loop.call_later(SCHEDULER_QUANTUM, self._schedule_cars)
