import requests
from typing import Union
from geoip2.database import Reader
from geoip2.errors import AuthenticationError
from geoip2.webservice import Client


class MaxmindClient:
    def __init__(self, license_key: str):
        self.license_key = license_key
        self.client = None

    def get_client(self):
        try:
            self._get_client()
        except AuthenticationError as auth_err:
            raise ValueError(f"Error whilst authenticating Maxmind", auth_err)

    def _get_client(self) -> Union[Reader, Client]:
        pass


class MaxmindDatabase(MaxmindClient):
    def __init__(self, license_key: str):
        super().__init__(license_key)

    def _get_client(self) -> Reader:
        if self.client is None:
            self._download_database()
            self.client = self._get_database_reader_from_path(
                "/opt/opencti-connector-maxmind/GeoIP2-City.mmdb"
            )
        return self.client

    def _download_database(self):
        url = f"https://download.maxmind.com/app/geoip_download"
        params = {
            "edition_id": "GeoIP2-City",
            "suffix": "mmdb",
            "license_key": self.license_key,
        }
        requests.get(url=url, params=params)

    @staticmethod
    def _get_database_reader_from_path(path) -> Reader:
        with Reader(path) as reader:
            return reader


class MaxmindWebservice(MaxmindClient):
    def __init__(self, account_id: int, license_key: str):
        self.account_id = account_id
        super().__init__(license_key)

    def _get_client(self):
        if self.client is None:
            with Client(self.account_id, self.license_key) as client:
                self.client = client
        return self.client
