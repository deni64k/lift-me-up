import ujson as json


class SimpleJsonRpc(object):
    def __init__(self, data):
        if (isinstance(data, str)):
            data = json.loads(data)
        self._id = data['id']
        self._method = data['method']
        self._params = data.get('params', dict())

    @property
    def method(self):
        return self._method

    @property
    def params(self):
        return self._params
