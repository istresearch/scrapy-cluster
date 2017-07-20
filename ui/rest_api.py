# class for interacting with the Scrapy Cluster REST API
import requests
from requests.exceptions import RequestException, \
                                ConnectionError, \
                                Timeout, \
                                TooManyRedirects


class SCRestAPI(object):

    _index_path = '/'
    _feed_path = '/feed'
    _poll_path = '/poll'

    def __init__(self, endpoint, timeout=3.05, read_timeout=10):
        self._endpoint = endpoint
        self._timeout = timeout
        self._read_timeout = read_timeout

    def _send_request(self, method='GET', path=_index_path, data=None):
        error = None
        try:
            req = requests.request(method=method,
                                   url=self._endpoint + path,
                                   json=data,
                                   timeout=(self._timeout,
                                            self._read_timeout))
            data = req.json()
            return data

        except ConnectionError:
            error = "Connection Error"
        except Timeout:
            error = "Request Timeout"
        except TooManyRedirects:
            error = "Too many redirects"
        except RequestException:
            error = "Unknown Request Exception"
        except ValueError:
            error = "JSON Decoding Error"

        final_result = {
            "status": "FAILURE",
            "data": None,
            "error": {
                "message": error
            }
        }
        return final_result

    def index(self):
        """
        Hits the index endpoint

        :returns: dict of results
        """
        return self._send_request()

    def feed(self, data=None):
        """
        Feeds JSON data into the feed endpoint
        """
        return self._send_request(method='POST', path=self._feed_path,
                                  data=data)

    def poll(self, data=None):
        """
        Feeds JSON data into the poll endpoint
        """
        return self._send_request(method='POST', path=self._poll_path,
                                  data=data)






