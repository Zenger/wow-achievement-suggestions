# SPDX-License-Identifier: MIT
import json
import requests

with open('config.json', 'r') as f:
    config = json.load(f)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 '
                  'Safari/537.36',
    "Upgrade-Insecure-Requests": "1", "DNT": "1",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate"}


class Scraper:
    auth_token: str = None
    headers: dict = HEADERS

    def __init__(self):
        self.client_id = config.get('wow').get('client_id')
        self.client_secret = config.get('wow').get('client_secret')
        self.region = config.get('wow').get('region')
        self.locale = config.get('wow').get('locale')
        self.base_url = f"https://{self.region}.api.blizzard.com"

        if any([self.client_id, self.client_secret, self.region]) is None:
            raise Exception("Missing environment variables")

        if not self.auth_token:
            self.set_auth_token()

    def set_auth_token(self):
        request = requests.post(
            "https://us.battle.net/oauth/token",
            headers=HEADERS.copy(),
            data={
                "grant_type": "client_credentials"
            },
            auth=(self.client_id, self.client_secret)
        )

        if request.status_code == 200:
            if request.json().get("access_token"):
                self.auth_token = request.json().get("access_token")
                self.headers["Authorization"] = f"Bearer {self.auth_token}"
            else:
                raise Exception("Failed to get access token")

    def get_character_achievements(self, realm: str, character: str):
        print(self.headers)
        print(f"{self.base_url}/profile/wow/character/{realm}/{character}/achievements")
        request = requests.get(
            f"{self.base_url}/profile/wow/character/{realm}/{character}/achievements",
            headers=self.headers,
            params={
                "namespace": "profile-" + self.region,
                "locale": self.locale
            }
        )

        print(request)

        if request.status_code == 200:
            return request.json()
        else:
            raise Exception("Failed to get character achievements")

    def get_achievement_data(self, achievement_id: int):
        request = requests.get(
            f"https://us.api.blizzard.com/data/wow/achievement/{achievement_id}?namespace=static-{self.region}&locale={self.locale}",
            headers=self.headers
        )

        if request.status_code == 200:
            return request.json()
        else:
            raise Exception("Failed to get achievement data")

    def request_account_profile(self):
        print('test')
