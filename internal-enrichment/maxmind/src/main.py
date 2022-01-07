import os
import yaml
import time
from typing import Dict, Tuple
from pycti import OpenCTIConnectorHelper, get_config_variable
from maxmind import MaxmindImporter, MaxmindDatabase, MaxmindWebservice


class MaxmindConnector:
    def __init__(self):
        self.helper = self._get_helper()
        self.args = self._get_args(
            "maxmind_data_source", "maxmind_license_key", "maxmind_account_id"
        )
        self.client = self._get_client()

    def _get_helper(self) -> OpenCTIConnectorHelper:
        # Instantiate the connector helper from config
        config_file_path = os.path.dirname(os.path.abspath(__file__)) + "/config.yml"
        self.config = (
            yaml.load(open(config_file_path), Loader=yaml.FullLoader)
            if os.path.isfile(config_file_path)
            else {}
        )
        return OpenCTIConnectorHelper(self.config)

    def _get_args(self, *args: str) -> Dict:
        arg_dict = {}
        for argument in args:
            arg_dict[argument] = get_config_variable(
                argument.upper(), ["maxmind", argument.lower()], self.config
            )
        return arg_dict

    def _get_client(self):
        datasource, license_key, account_id = (
            self.args["maxmind_data_source"],
            self.args["maxmind_license_key"],
            self.args["maxmind_account_id"],
        )
        if datasource == "DATABASE":
            self.client = MaxmindDatabase(license_key)
        elif datasource == "API":
            self.client = MaxmindWebservice(account_id, license_key)
        else:
            raise ValueError("Maxmind datasource must be either 'API' or 'DATABASE'")

    def _process_message(self, data: Dict) -> str:
        entity_id = data.get("entity_id")
        importer = MaxmindImporter(entity_id, self.client, self.helper)
        return importer.process_message()

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
