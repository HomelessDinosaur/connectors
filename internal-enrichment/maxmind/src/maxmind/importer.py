import geoip2
from pycti import OpenCTIConnectorHelper

from stix2 import Bundle
from geoip2.webservice import GeoIP2Error, City
from client import MaxmindClient
from builder import MaxmindBuilder
from typing import Dict


class MaxmindImporter:
    def __init__(
        self, entity_id: str, client: MaxmindClient, helper: OpenCTIConnectorHelper
    ):
        self.client = client.get_client()
        self.helper = helper
        self.observable: Dict = self._get_observable_from_entity_id(entity_id)

    def _get_observable_from_entity_id(self, entity_id: str):
        return self.helper.api.stix_cyber_observable.read(id=entity_id)

    def process_message(self) -> str:
        if self._check_observable_contains_ip_address():
            return self._update_ip_address_observable()
        return "Observable was not an IP Address"

    def _check_observable_contains_ip_address(self) -> bool:
        entity_type = self.observable.get("entity_type").lower()
        if entity_type == "ipv4-addr" or entity_type == "ipv6-addr":
            return True
        return False

    def _update_ip_address_observable(self) -> str:
        ip_address = self.observable.get("value")
        try:
            self._update_observable_location_data(ip_address)
            return "Observable was successfully tagged with geolocation data"
        except GeoIP2Error:
            return f"Location for IP Address {ip_address} could not be found"

    def _update_observable_location_data(self, ip_address: str):
        response = self._retrieve_location_data_from_ip_address(ip_address)
        bundles_sent = self._send_bundle_to_opencti_worker(response)
        self.helper.log_debug(f"Bundle information sent: {bundles_sent}")
        self.helper.log_info(
            f"Sent {str(len(bundles_sent))} stix bundle(s) for worker import"
        )

    def _retrieve_location_data_from_ip_address(self, ipv4_address) -> City:
        return self.client.city(ipv4_address)

    def _send_bundle_to_opencti_worker(
        self, geo_ip_data: geoip2.webservice.City
    ) -> list:
        bundler = MaxmindBuilder(self.helper)
        country_location = bundler.country(geo_ip_data.country)
        city_location = bundler.city(geo_ip_data.city)
        bundler.relationship(city_location.id, country_location.id)
        bundler.relationship(self.observable.get("standard_id"), city_location.id)
        return bundler.send()
