import time
import logging

from django.conf import settings

from twocaptcha import TwoCaptcha

from .exceptions import RecaptchaRetiesError, RecaptchaBalanceError


class ReCaptchaService:
    """ Recaptcha service """

    def __init__(self):
        self.recaptcha_solver = TwoCaptcha(settings.RECAPTCHA_API_KEY)
        self.logger = logging.getLogger(__name__)

    def recaptcha_solving(self, url):
        counter = 0
        while counter < settings.MAX_RECAPTCHA_RETRIES:
            try:
                result_solving = self.recaptcha_solver.recaptcha(sitekey=settings.SITE_KEY, url=url)
                result_code = result_solving['code']
                return result_code
            except Exception as e:
                self.logger.error(e)
                counter += 1
                time.sleep(5)

        raise RecaptchaRetiesError(message='Recaptcha error', status=settings.ERROR_STATUS)

    def balance(self):
        counter = 0
        while counter < settings.MAX_BALANCE_RETRIES:
            try:
                balance = self.recaptcha_solver.balance()
                return balance
            except Exception as e:
                self.logger.error(e)
                time.sleep(3)

        raise RecaptchaBalanceError(message='Little balance', status=settings.ERROR_STATUS)
