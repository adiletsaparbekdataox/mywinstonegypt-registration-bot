class BotError(Exception):
    """ Base class for other exceptions """

    def __init__(self, message: str, status: str):
        self.message = message
        self.status = status
        super().__init__(self.message, self.status)

    def __str__(self):
        return self.message


class RecaptchaRetiesError(BotError):
    """ Number of retries exceeded recaptcha solution """
    pass


class RecaptchaBalanceError(BotError):
    """ Little balance or error request for get balance"""
    pass


class RequestError(BotError):
    """ Request server error """
    pass


class RegistrationError(BotError):
    """ Invalid registration """


class SiteError(BotError):
    """ Website not work """
    pass


class InvalidVideoUrl(BotError):
    """ Invalid video url """
    pass
