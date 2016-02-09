from hoplite.serializer import hoplite_dumps
from hoplite.exceptions import InternalServerError
import requests


class ClientMixin(object):
    def _json_data(self, kwargs):
        if 'data' in kwargs:
            kwargs['data'] = hoplite_dumps(kwargs['data'])
        if not kwargs.get('headers', None):
            kwargs['headers'] = {'Content-type': 'application/json'}
        return kwargs

    def _raise_if_status_500(self, response):
        if response.status_code == 500:
            raise InternalServerError()
        return response

    def _request(self, method, *args, **kwargs):
        return self._raise_if_status_500(method(*args, **kwargs))

    def _jrequest(self, *args, **kwargs):
        return self._request(*args, **kwargs)

    def jget(self, *args, **kwargs):
        return self._jrequest(requests.get, *args, **kwargs)

    def jpost(self, *args, **kwargs):
        return self._jrequest(requests.post, *args, **self._json_data(kwargs))

    def jput(self, *args, **kwargs):
        return self._jrequest(requests.put, *args, **self._json_data(kwargs))

    def jpatch(self, *args, **kwargs):
        return self._jrequest(requests.patch, *args, **self._json_data(kwargs))

    def jdelete(self, *args, **kwargs):
        return self._jrequest(requests.delete, *args, **self._json_data(kwargs))
