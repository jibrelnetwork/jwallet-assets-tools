"""
Ugly hack to increase pool size for requests.Session.
"""
import lru
import requests
from requests.adapters import HTTPAdapter
from web3 import HTTPProvider
from web3.utils.caching import generate_cache_key


def _remove_session(key, session):
    session.close()


_session_cache = lru.LRU(8, callback=_remove_session)


def _get_session(*args, **kwargs):
    cache_key = generate_cache_key((args, kwargs))
    if cache_key not in _session_cache:
        session = requests.Session()
        session.mount('https://', HTTPAdapter(
            pool_connections=50, pool_maxsize=100, max_retries=0, pool_block=True
        ))
        _session_cache[cache_key] = session
    return _session_cache[cache_key]


def make_post_request(endpoint_uri, data, *args, **kwargs):
    kwargs.setdefault('timeout', 10)
    session = _get_session(endpoint_uri)
    response = session.post(endpoint_uri, data=data, *args, **kwargs)
    response.raise_for_status()

    return response.content


class CustomHTTPProvider(HTTPProvider):
    def make_request(self, method, params):
        self.logger.debug("Making request HTTP. URI: %s, Method: %s",
                          self.endpoint_uri, method)
        request_data = self.encode_rpc_request(method, params)
        raw_response = make_post_request(
            self.endpoint_uri,
            request_data,
            **self.get_request_kwargs()
        )
        response = self.decode_rpc_response(raw_response)
        self.logger.debug("Getting response HTTP. URI: %s, "
                          "Method: %s, Response: %s",
                          self.endpoint_uri, method, response)
        return response
