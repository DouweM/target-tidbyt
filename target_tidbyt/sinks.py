from __future__ import annotations
import os
from pathlib import Path

import yaml

"""tidbyt target sink class, which handles writing streams."""

import requests

from singer_sdk.sinks import RecordSink


class TidbytSink(RecordSink):
    """tidbyt target sink class."""

    def process_record(self, record: dict, context: dict) -> None:
        """Process the record.

        Args:
            record: Individual record in the stream.
            context: Stream partition or context dictionary.
        """
        # Sample:
        # ------
        # client.write(record)  # noqa: ERA001

        if "image_data" not in record:
            raise ValueError("No image data found in record")

        devices = self.get_devices()

        device_names = self._config.get("device_names")
        if device_names:
            devices = [device for device in devices if device.get("name") in device_names]

        for device in devices:
            self.send_to_tidbyt(record, device)

    def get_devices_from_file(self):
        devices_path_raw = self._config.get("devices_path")
        if not devices_path_raw:
            return []

        devices_path = Path(devices_path_raw)
        if not devices_path.exists():
            return []

        devices_config = yaml.safe_load(devices_path.read_text())

        if isinstance(devices_config, list):
            devices_config = {"devices": devices_config}
        devices = devices_config.get("devices") or []

        def expand_env_var(value):
            if isinstance(value, str) and value.startswith("$"):
                return os.getenv(value[1:])
            return value

        return [
            {
                "name": device.get("name"),
                "id": expand_env_var(device.get("id")),
                "token": expand_env_var(device.get("token")),
            }
            for device in devices
        ]

    def get_devices(self):
        return self.get_devices_from_file() or [
            {
                "name": "default",
                "id": self._config.get("device_id"),
                "token": self._config.get("token")
            }
        ]

    def send_to_tidbyt(self, record, device):
        image_data = record.get("image_data", "")

        device_name = device.get("name")
        device_id = device.get("id")
        token = device.get("token")

        installation_id = record.get("installation_id")
        if installation_id:
            installation_id = installation_id.replace("-", "") # Must be alphanumeric
        background = record.get("background", True) # TODO: Take from config

        if image_data:
            payload = {
                "image": image_data,
                "installationID": installation_id,
                "background": background
            }

            self.logger.info("Pushing image to Tidbyt device '%s' (%s): %s", device_name, device_id, payload)

            response = requests.post(
                "https://api.tidbyt.com/v0/devices/%s/push" % device_id,
                json=payload,
                headers={
                    "Authorization": "Bearer %s" % token,
                }
            )
            self.logger.info("Response: %s", response.text)
            response.raise_for_status()
        elif installation_id:
            self.logger.info("Deleting installation from Tidbyt device '%s' (%s): %s", device_name, device_id, installation_id)

            response = requests.delete(
                "https://api.tidbyt.com/v0/devices/%s/installations/%s" % (device_id, installation_id),
                headers={
                    "Authorization": "Bearer %s" % token,
                }
            )
            if response.status_code == 500 and response.json().get('message') == 'installation not found':
                self.logger.info("Installation not found, skipping")
            else:
                self.logger.info("Response: %s", response.text)
                response.raise_for_status()
        else:
            self.logger.info("No image data or installation ID found in record")

