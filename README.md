Lift Me Up
==========

**[Демо](http://lift-me-up.illiteracy.ru/)**

**[«О приложении»](http://lift-me-up.illiteracy.ru/#about)**

Установка
---------

Для работы приложения необходим Python 3.4. Его можно поставить из доступного репозитория или pyenv.
Установив Python 3.4, нужно создать виртуальное окружение в каталоге проекта:
```bash
git clone https://github.com/neglectedvalue/lift-me-up
cd lift-me-up
pyvenv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Теперь приложение должно быть готово к запуску

Запуск
------

Приложение запускается с помощью run.py:
```bash
python run.py
```

И открываем в браузере:
```bash
open http://localhost:8080
```

Немного слов о коде
-------------------

Код писался в компромиссе между поиграться с новым и решить задачу.

Поэтому я решил воспользоваться стандартной реализацией ассионхроного ввода-вывода [asyncio](https://docs.python.org/3/library/asyncio.html) из свежей версии Питона. Для HTTP API я взял маленький веб-фреймворк [Vase](https://github.com/neglectedvalue/Vase), а для веб-интерфейса — [Zurb Foundation](http://foundation.zurb.com), [jQuery](http://jquery.com/) и [Underscore.js](http://underscorejs.org). К сожалению, в некоторых местах я не совладал с вёрсткой и не стал тратить на это время, но, по-моему, получилось симпатичненько.

Лифты и здания реализованы в отдельных моделях `Car` и `Building`, соответственно. Логика шедулинга вынесена в класс `Scheduler`. Сама процедура планирования описана в [«О приложении»](http://illiteracy.ru:8080/#about). Состояние зданий регулярно сохранятся в файле `state.pickle`.

Деплой производит простым скриптом `deploy.sh`.

HTTP API
--------

    POST /api/v1/buildings/{building}/cars/{car}/buttons/{floor}
Отправляет лифт `car` на этаж `floor` в здании `building`.

    POST /api/v1/buildings/{building}/cars/{car}/buttons/toggle
Выключает или включает лифт `car` в здании `building`.

    POST /api/v1/buildings/{building}/floors/{floor}/buttons/call
Вызывает лифт на этаж `floor` в здании `building`.

    POST /api/v1/buildings
    {
        "n_cars": "8"
        "n_floors": "8"
        "name": "celod-ridge"
        "speed": "1.4"
    }
Создаёт здание с указанными параметрами.

    DELETE /api/v1/buildings/{building}
Сносит здание `building`.

    GET /api/v1/buildings/{building}/status
    {
        "status": {
            "n_floors": 12,
            "floors": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            "name": "sufufo-junction",
            "n_cars": 6,
            "cars": [{
                "speed": 1.0,
                "floor": 11,
                "status": "standby",
                "floor_approximated": 11,
                "destinations": [],
                "backlog": [5, 11, 9, 6, 11, 9, 11],
                "capability": 250,
                "direction": null
            }, {
                ...
            }]
        }
    }
Возвращает состояние лифтов в здании `building`.

    GET /api/v1/status
Возвращает состояние лифтов во всех зданиях.
    
    GET /ws
Открывает WebSocket для подписки на актуальное состояние лифтов.
