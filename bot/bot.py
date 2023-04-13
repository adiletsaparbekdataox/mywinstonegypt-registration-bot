import logging
import random

import requests
from django.conf import settings

from requests import request
from parsel import Selector

from .services import ReCaptchaService
from .exceptions import *
from .utils import format_birthday, format_phone_number


base_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:96.0) Gecko/20100101 Firefox/96.0',
    'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
    'Content-Type': 'application/json;charset=utf-8',
    'Origin': 'https://mywinstonegypt.com',
    'Referer': 'https://mywinstonegypt.com/'
}


class Bot:
    """ Bot for creat account on mywinstonegypt """

    MAIN_URL = 'https://mywinstonegypt.com/login'
    MAIN_VIDEO_URL = 'https://mywinstonegypt.com/watch?v={}'
    SINGUP_URL = 'https://auth.mywinstonegypt.com/v1/signup'

    VIDEO_ELEMENT_XPATH = '//div[contains(@class, "plyr__controls")]'
    VALID_VIDEO_IDS = [148, 147, 146, 1, 2, 3, 4, 5, 6, 115]

    SUCCESS_TASK = {'status': settings.SUCCESS_STATUS, 'message': 'Task done'}

    def __init__(self, language: str, firstname: str, lastname: str, birthday: str, email: str,
                 phone_number: int, password: str, preference: str, referral_code: str,
                 video_url: str, only_registration: bool, over_18: str, smoker: str,
                 proxy: str) -> None:
        self.language = language
        self.over_18 = over_18
        self.smoker = smoker
        self.firstname = firstname
        self.lastname = lastname
        self.birthday = format_birthday(birthday)
        self.email = email
        self.phone_number = format_phone_number(phone_number)
        self.password = password
        self.preference = preference
        self.referral_code = referral_code
        self.only_registration = only_registration
        self.video_url = video_url
        self.proxies = {'http': proxy, 'https': proxy}

        self.recaptcha_token = None
        self.site_access_parameters = {}

        self.logger = logging.getLogger(__name__)
        self.recaptcha = ReCaptchaService()

    @staticmethod
    def send_request(method: str, url: str, proxies: dict, payload: dict = None,
                     headers: dict = base_headers) -> requests.Response:
        counter = 0
        while counter < settings.MAX_REQUEST_RETRIES:
            try:
                response = request(method=method, url=url, headers=headers, json=payload,
                                   proxies=proxies)
                if response.status_code >= 500:
                    continue
                return response
            except Exception as exc:
                counter += 1
        raise RequestError(status=settings.ERROR_STATUS, message='Max request retries')

    def generate_payload(self):
        return {
            'language': self.language,
            'first_name': self.firstname,
            'last_name': self.lastname,
            'dob': self.birthday,
            'email': self.email,
            'phone_number': self.phone_number,
            'password': self.password,
            'confirm_password': self.password,
            'smoking_pref': self.preference,
            'recaptcha': self.recaptcha_token
        }

    def generate_video_cookie(self):
        cookie = ''
        cookie += f"token={self.site_access_parameters['access_token']}; "
        cookie += f"refresh_token={self.site_access_parameters['refresh_token']}; "
        cookie += f"user_info={{%22id%22:%22{self.site_access_parameters['id']}%22%2C%22"
        cookie += f"generated_id%22:%22{self.lastname}{self.site_access_parameters['code']}%22%2C%22"
        cookie += f"first_name%22:%22{self.firstname}%22%2C%22last_name%22:%22{self.lastname}%22%2C%22"
        cookie += f"dob%22:%22{self.birthday}%22%2C%22email%22:%22{self.email}%22%2C%22"
        cookie += f"phone_number%22:%22{self.phone_number}%22%2C%22"
        cookie += f"image_url%22:%22https://static.mywinstonegypt.com/images/placeholder.jpg%22%2C%22"
        cookie += f"smoking_pref%22:%22{self.preference}%22%2C%22"
        cookie += f"code%22:%22{self.site_access_parameters['code']}%22%2C%22total_coins%22:%220%22%2C%22"
        cookie += f"total_eagles%22:%220%22%2C%22language%22:%22{self.language}%22%2C%22"
        cookie += f"friends_count%22:0}}"
        return cookie

    def generate_response_result(self, message, status=settings.ERROR_STATUS) -> dict:
        return {
            'language': self.language,
            'over_18': self.over_18,
            'smoker': self.smoker,
            'firstname': self.firstname,
            'lastname': self.lastname,
            'birthday': self.birthday,
            'email': self.email,
            'phone_number': self.phone_number,
            'password': self.password,
            'preference': self.preference,
            'referral_code': self.referral_code,
            'only_registration': self.only_registration,
            'video_url': self.video_url,
            'message': message,
            'status': status
        }

    def open_video_page(self):
        if self.video_url is not None:
            pass
        else:
            self.video_url = self.MAIN_VIDEO_URL.format(
                random.choice(self.VALID_VIDEO_IDS)
            )

        base_headers['cookie'] = self.generate_video_cookie()
        video_page_response = self.send_request(
            method='GET',
            url=self.video_url,
            headers=base_headers,
            proxies=self.proxies,
            payload=self.generate_payload()
        )

        tree = Selector(text=video_page_response.text)
        video_element = tree.xpath(self.VIDEO_ELEMENT_XPATH)
        if video_element is None:
            self.logger.error('Video url invalid')
            raise InvalidVideoUrl(status=settings.ERROR_STATUS, message='Video url invalid')
        self.logger.info('Video is opened')

    def start(self):
        recaptcha_balance = self.recaptcha.balance()
        self.logger.info(f'Recaptcha balance: {recaptcha_balance}')
        if recaptcha_balance < settings.RECAPTCHA_SERVICE_MIN_BALANCE:
            raise RecaptchaBalanceError(
                status=settings.ERROR_STATUS,
                message='Little recaptcha service balance'
            )

        self.recaptcha_token = self.recaptcha.recaptcha_solving(url=self.MAIN_URL)
        registration_response = self.send_request(
            method='POST',
            url=self.SINGUP_URL,
            proxies=self.proxies,
            payload=self.generate_payload()
        ).json()

        if registration_response is None:
            raise SiteError(status=settings.ERROR_STATUS, message='Website not working')

        status = registration_response.get('status')

        if status:
            raise RegistrationError(
                status=settings.ERROR_STATUS,
                message=f'{registration_response["title"]} [{registration_response["message"]}]'
            )

        self.site_access_parameters['id'] = registration_response['id']
        self.site_access_parameters['code'] = registration_response['code']
        self.site_access_parameters['access_token'] = registration_response['token']
        self.site_access_parameters['refresh_token'] = registration_response['refresh_token']

        if self.only_registration:
            return self.SUCCESS_TASK

        self.open_video_page()
        return self.SUCCESS_TASK

    def main(self) -> dict:
        try:
            result = self.start()
            message = result['message']
            status = result['status']
        except RequestError as exc:
            message = exc.message
            status = exc.status
        except RegistrationError as exc:
            message = exc.message
            status = exc.status
        except SiteError as exc:
            message = exc.message
            status = exc.status
        except Exception as exc:
            message = exc
            status = settings.ERROR_STATUS

        response = self.generate_response_result(message=message, status=status)
        self.logger.info(f'Email: {self.email} | Message: {message} | Status: {status}')

        return response
