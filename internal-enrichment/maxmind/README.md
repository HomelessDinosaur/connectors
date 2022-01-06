# OpenCTI Template Connector

Using the maxmind internal-enrichment connector, observables that contain IPv4 or IPv6 addresses are updated with geolocation data.
This is done using Maxmind's GeoIP2 databases or their webservice API.

## Installation

### Requirements

- OpenCTI Platform >= 5.1.3
- Maxmind GeoIP2 >= 4.5.0

### Configuration

| Parameter                    | Docker envvar                | Mandatory | Description                                                                                             |
|------------------------------|------------------------------|-----------|---------------------------------------------------------------------------------------------------------|
| `opencti_url`                | `OPENCTI_URL`                | Yes       | The URL of the OpenCTI platform.                                                                        |
| `opencti_token`              | `OPENCTI_TOKEN`              | Yes       | The default admin token configured in the OpenCTI platform parameters file.                             |
| `connector_id`               | `CONNECTOR_ID`               | Yes       | A valid arbitrary `UUIDv4` that must be unique for this connector.                                      |
| `connector_type`             | `CONNECTOR_TYPE`             | Yes       | Must be `Template_Type` (this is the connector type).                                                   |
| `connector_name`             | `CONNECTOR_NAME`             | Yes       | Option `Template`                                                                                       |
| `connector_scope`            | `CONNECTOR_SCOPE`            | Yes       | Supported scope: Template Scope (MIME Type or Stix Object)                                              |
| `connector_confidence_level` | `CONNECTOR_CONFIDENCE_LEVEL` | Yes       | The default confidence level for created sightings (a number between 1 and 4).                          |
| `connector_log_level`        | `CONNECTOR_LOG_LEVEL`        | Yes       | The log level for this connector, could be `debug`, `info`, `warn` or `error` (less verbose).           |
| `maxmind_data_source`        | `MAXMIND_DATA_SOURCE`        | Yes       | Choose between maxmind calling from the api (API) and searching a local maxmind database (DATABASE)     |
| `maxmind_account_id`         | `MAXMIND_ACCOUNT_ID`         | No        | The Maxmind account id used to connect to the Maxmind Api. Not necessary for connecting to the database |
| `maxmind_license_key`        | `MAXMIND_LICENSE_KEY`        | Yes       | The Maxmind license key used to connect to the Maxmind Api or initialize the maxmind Database           |


### Debugging ###
For debugging purposes set CONNECTOR_LOG_LEVEL to debug.

### Additional information
This connector can use a local maxmind data source or by making calls to the maxmind webservice api. This can be toggled with
the maxmind datasource configuration variable. The license key must be set regardless of the datasource used, but if the Api
is used then the account id must also be set.

If the local database is used, a request will be made when the connector starts
to get the most updated GeoIP2-City database in .mmdb form. This may cause the connector to take a bit longer on start up.
