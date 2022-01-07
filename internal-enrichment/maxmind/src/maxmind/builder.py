from stix2 import Relationship, Location, Bundle
import geoip2.database
from pycti import OpenCTIStix2Utils, OpenCTIConnectorHelper


class MaxmindBuilder:
    def __init__(self, helper: OpenCTIConnectorHelper):
        self.stix_objects = []
        self.helper = helper
        pass

    def country(self, country: geoip2.database.Country) -> Location:
        country_location = Location(
            id=OpenCTIStix2Utils.generate_random_stix_id("location"),
            name=country.country.name,
            country=country.country.name,
            custom_properties={
                "x_opencti_location_type": "Country",
                "x_opencti_aliases": [country.country.name],
            },
        )
        self.stix_objects.append(country_location)
        return country_location

    def city(self, city: geoip2.database.City) -> Location:
        city_location = Location(
            id=OpenCTIStix2Utils.generate_random_stix_id("location"),
            name=city.city.name
            if city.city.name is None
            else city.subdivisions.most_specific.name,
            country=city.country.name,
            latitude=city.location.longitude,
            longitude=city.location.latitude,
            custom_properties={"x_opencti_location_type": "City"},
        )
        self.stix_objects.append(city_location)
        return city_location

    def relationship(self, source_id: str, target_id) -> Relationship:
        relationship = Relationship(
            id=OpenCTIStix2Utils.generate_random_stix_id("relationship"),
            relationship_type="located-at",
            source_ref=source_id,
            target_ref=target_id,
        )
        self.stix_objects.append(relationship)
        return relationship

    def bundle(self) -> Bundle:
        return Bundle(
            objects=self.stix_objects,
            allow_custom=True,
        )

    def send(self) -> list:
        return self.helper.send_stix2_bundle(self.bundle().serialize())
