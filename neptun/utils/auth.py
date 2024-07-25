import httpx


class NeptunAuth(httpx.Auth):
    def __init__(self, token):
        self.token = token

    def auth_flow(self, request):
        request.headers['X-Authentication'] = self.token
        yield request