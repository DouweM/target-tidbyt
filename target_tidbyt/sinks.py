from __future__ import annotations

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

        image_data = record.get("image_data", "")

        token = self._config.get("token")
        device_id = self._config.get("device_id")

        installation_id = record.get("installation_id")
        if installation_id:
            installation_id = installation_id.replace("-", "") # Must be alphanumeric
        background = record.get("background", True)

        if image_data:
            payload = {
                "image": image_data,
                "installationID": installation_id,
                "background": background
            }

            self.logger.info("Pushing image to Tidbyt device '%s': %s", device_id, payload)

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
            self.logger.info("Deleting installation from Tidbyt device '%s': %s", device_id, installation_id)

            response = requests.delete(
                "https://api.tidbyt.com/v0/devices/%s/installations/%s" % (device_id, installation_id),
                headers={
                    "Authorization": "Bearer %s" % token,
                }
            )
            self.logger.info("Response", response, response.text)
            if response.status_code == 500 and response.json().get('message') == 'installation not found':
                self.logger.info("Installation not found, skipping")
            else:
                response.raise_for_status()
        else:
            self.logger.info("No image data or installation ID found in record")

