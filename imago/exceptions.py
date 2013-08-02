
class APIError(Exception):

    def __init__(self, msg, status=400):
        self.msg = msg
        self.status = status

    def __str__(self):
        return str(self.msg)


