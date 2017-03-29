from scrapy.downloadermiddlewares.cookies import CookiesMiddleware


class CustomCookiesMiddleware(CookiesMiddleware):
    '''
    Custom Cookies Middleware to pass our required cookies along but not
    persist between calls
    '''

    def process_request(self, request, spider):
        if 'dont_merge_cookies' in request.meta:
            return

        cookiejarkey = request.meta.get("cookiejar")
        jar = self.jars[cookiejarkey]
        jar.clear()  # custom line
        cookies = self._get_request_cookies(jar, request)
        for cookie in cookies:
            jar.set_cookie_if_ok(cookie, request)

        # set Cookie header
        request.headers.pop('Cookie', None)
        jar.add_cookie_header(request)

        self._debug_cookie(request, spider)
