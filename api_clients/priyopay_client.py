import json
import time
from json import JSONDecodeError

import requests
from django.conf import settings


class PriyoPayClient:
    def __init__(self):
        self._base_url = settings.PRIYOPAY_API_URL
        self._api_key = settings.PRIYOPAY_API_KEY

    def __remote_call(self, endpoint, method, payload=None, raise_for_status=True):
        url = self._base_url + endpoint

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "x-api-key": self._api_key
        }

        payload = payload if payload else {}
        payload = json.dumps(payload, default=str)

        response = requests.request(method.upper(), url, data=payload, headers=headers)

        if raise_for_status:
            response.raise_for_status()

        try:
            response_content = response.json()
        except JSONDecodeError:
            response_content = None

        return response_content, response.status_code

    def fetch_user_basic_info(self, user_id, **kwargs):
        url = f"/user-basic-info/{user_id}/"
        return self.__remote_call(url, "GET", **kwargs)

    def fetch_deposit_claims(self, **kwargs):
        url = f"/student/money-deposit-claim/"
        return self.__remote_call(url, "GET", **kwargs)


    def update_deposit_claims(self, claim_id, payload):
        url = f"/student/money-deposit-claim/{claim_id}/update-claim-status/"
        return self.__remote_call(url, "PATCH", payload=payload)

    def fetch_conversions(self, **kwargs):
        url = f"/student/bdt-to-usd-convert-request/"
        return self.__remote_call(url, "GET", **kwargs)

    def update_conversion(self, conversion_id, payload):
        url = f"/student/bdt-to-usd-convert-request/{conversion_id}/update-status/"
        return self.__remote_call(url, "PATCH", payload=payload)

    def create_conversion(self, payload):
        url = "/student/bdt-to-usd-convert-request/"
        return self.__remote_call(url, "POST", payload=payload)
