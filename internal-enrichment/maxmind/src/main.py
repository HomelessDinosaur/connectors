import os
import yaml
import time
import geoip2.webservice
from typing import Dict
from stix2 import Relationship, Location, Bundle
from pycti import OpenCTIConnectorHelper, OpenCTIStix2Utils, get_config_variable
from geoip2.webservice import Client, City, Country, GeoIP2Error, AuthenticationError


class MaxmindConnector:
    def __init__(self):
        # Instantiate the connector helper from config
        config_file_path = os.path.dirname(os.path.abspath(__file__)) + "/config.yml"
        config = (
            yaml.load(open(config_file_path), Loader=yaml.FullLoader)
            if os.path.isfile(config_file_path)
            else {}
        )
        self.helper = OpenCTIConnectorHelper(config)
        account_id = get_config_variable(
            "MAXMIND_ACCOUNT_ID",
            ["maxmind", "maxmind_account_id"],
            config,
            default=None,
        )
        if account_id is None:
            raise ValueError("Account ID must be provided")
        api_key = get_config_variable(
            "MAXMIND_API_KEY", ["maxmind", "maxmind_api_key"], config, default=None
        )
        if api_key is None:
            raise ValueError("API Key must be provided")
        try:
            self.client = self._get_maxmind_client(
                account_id=account_id, api_key=api_key
            )
            self.helper.log_debug("Successfully authenticated with Maxmind Client")
        except AuthenticationError:
            raise ValueError(
                "A valid account ID and license key are required to use Maxmind API"
            )

    @staticmethod
    def _get_maxmind_client(account_id: int, api_key: str) -> Client:
        with geoip2.webservice.Client(account_id, api_key) as client:
            return client

    def _process_message(self, data: Dict) -> str:
        entity_id = data.get("entity_id")
        observable = self._get_observable_from_entity_id(entity_id)
        if self._check_observable_contains_ip_address(observable):
            self.helper.log_debug(
                f"Observable with ID {entity_id} is contains an IP Address"
            )
            return self._update_ip_address_observable(observable)
        return "Observable was not an IP Address"

    def _get_observable_from_entity_id(self, entity_id: str):
        return self.helper.api.stix_cyber_observable.read(id=entity_id)

    @staticmethod
    def _check_observable_contains_ip_address(observable: Dict) -> bool:
        entity_type = observable.get("entity_type").lower()
        if entity_type == "ipv4-addr" or entity_type == "ipv6-addr":
            return True
        return False

    def _update_ip_address_observable(self, observable: Dict) -> str:
        observable_id, ip_address = self._extract_information_from_observable(
            observable, "standard_id", "ip_address"
        )
        try:
            self.helper.log_debug(
                f"Observable '{observable_id}' contains IP Address '{ip_address}'"
            )
            self._update_observable_location_data(observable_id, ip_address)
            return "Observable was successfully tagged with geolocation data"
        except GeoIP2Error:
            return f"Location for IP Address {ip_address} could not be found"

    @staticmethod
    def _extract_information_from_observable(observable: Dict, *args) -> tuple:
        return tuple(map(lambda key: observable.get(key), args))

    def _update_observable_location_data(self, observable_id: str, ip_address: str):
        response = self._retrieve_location_data_from_ip_address(ip_address)
        bundle = self._generate_stix_bundle(
            observable_id=observable_id, geoip_response=response
        )
        bundles_sent = self.helper.send_stix2_bundle(bundle.serialize())
        self.helper.log_debug(f"Bundle information sent: {bundle.serialize()}")
        self.helper.log_info(
            f"Sent {str(len(bundles_sent))} stix bundle(s) for worker import"
        )

    def _retrieve_location_data_from_ip_address(self, ipv4_address) -> City:
        return self.client.city(ipv4_address)

    def _generate_stix_bundle(self, observable_id, geoip_response: City) -> Bundle:
        country_location = self._create_stix_country(geoip_response.country)
        city_location = self._create_stix_city(geoip_response.city)
        city_to_country = self._create_stix_relationship(
            city_location.id, country_location.id
        )
        observable_to_city = self._create_stix_relationship(
            observable_id, city_location.id
        )
        return self._bundle_stix_objects(
            country_location, city_location, city_to_country, observable_to_city
        )

    @staticmethod
    def _create_stix_country(country: Country) -> Location:
        return Location(
            id=OpenCTIStix2Utils.generate_random_stix_id("location"),
            name=country.country.name,
            country=country.country.name,
            custom_properties={
                "x_opencti_location_type": "Country",
                "x_opencti_aliases": [country.country.name],
            },
        )

    @staticmethod
    def _create_stix_city(city: City) -> Location:
        return Location(
            id=OpenCTIStix2Utils.generate_random_stix_id("location"),
            name=city.city.name
            if city.city.name is None
            else city.subdivisions.most_specific.name,
            country=city.country.name,
            latitude=city.location.longitude,
            longitude=city.location.latitude,
            custom_properties={"x_opencti_location_type": "City"},
        )

    @staticmethod
    def _create_stix_relationship(source_id: str, target_id) -> Relationship:
        return Relationship(
            id=OpenCTIStix2Utils.generate_random_stix_id("relationship"),
            relationship_type="located-at",
            source_ref=source_id,
            target_ref=target_id,
        )

    @staticmethod
    def _bundle_stix_objects(*args) -> Bundle:
        return Bundle(
            objects=[*args],
            allow_custom=True,
        )

    # Start the main loop
    def start(self) -> None:
        self.helper.listen(self._process_message)


if __name__ == "__main__":
    try:
        connector = MaxmindConnector()
        connector.start()
    except Exception as e:
        print(e)
        time.sleep(10)
        exit(0)
