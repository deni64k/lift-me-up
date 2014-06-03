import asyncio

from lift_me_up.app import create_app
from lift_me_up.state import state
from lift_me_up.scheduler import Scheduler


def main():
    loop = asyncio.get_event_loop()

    scheduler = Scheduler(state)
    scheduler.run(loop=loop)

    app = create_app(state, scheduler)
    app.run(port=8080, loop=loop)

    loop.run_forever()
    loop.close()


if __name__ == '__main__':
    main()
