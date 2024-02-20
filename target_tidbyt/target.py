from __future__ import annotations

"""tidbyt target class."""

from singer_sdk import typing as th
from singer_sdk.target_base import Target

from target_tidbyt.sinks import (
    TidbytSink,
)


class TargetTidbyt(Target):
    """Sample target for tidbyt."""

    name = "target-tidbyt"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "device_id",
            th.StringType,
            description="Tidbyt device ID",
        ),
        th.Property(
            "token",
            th.StringType,
            description="Tidbyt API token",
        ),
        th.Property(
            "devices_path",
            th.StringType,
            description="Path to devices.yml defining devices with name, id, and token.",
        ),
        th.Property(
            "devices_names",
            th.ArrayType(th.StringType),
            description="Only send to these named devices. If not set, send to all devices.",
        )
    ).to_dict()

    default_sink_class = TidbytSink


if __name__ == "__main__":
    TargetTidbyt.cli()
