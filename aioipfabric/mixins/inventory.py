#  Copyright 2020 Jeremy Schulman
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

from dataclasses import dataclass

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------

from httpx import Response

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from aioipfabric.base_client import IPFBaseClient, table_api
from aioipfabric.consts import COLOR_GREEN, TableFields

# -----------------------------------------------------------------------------
#
#                                 CODE BEGINS
#
# -----------------------------------------------------------------------------


@dataclass
class URIs:
    """identifies API URL endpoings used"""

    devices = "/tables/inventory/devices"
    device_parts = "/tables/inventory/pn"
    managed_ipaddrs = "/tables/addressing/managed-devs"
    snapshots = "/snapshots"


DEFAULT_PARTS_COLUMNS = [
    "deviceSn",
    "hostname",
    "siteName",
    "name",
    "dscr",
    "pid",
    "sn",
    "vid",
    "vendor",
    "platform",
    "model",
]


class IPFInventoryMixin(IPFBaseClient):
    """
    IP Fabric client mixin supporting the inventory features.
        - devices
        - device optics
        - device managed IP addresses
    """

    @table_api
    async def fetch_devices(self, request: dict) -> Response:
        """
        Fetch <Inventory | Devices> table records.

        Parameters
        ----------
        request: dict
            The API body request payload, prepared by the table_api decorator

        Returns
        -------
        The HTTPx response, which will be post-processed by the table_api decorator.
        """

        default_columns = [
            "sn",
            "snHw",
            "hostname",
            "siteName",
            "loginIp",
            "loginType",
            "uptime",
            "vendor",
            "platform",
            "family",
            "version",
            "model",
        ]
        request.setdefault(TableFields.columns, default_columns)
        return await self.api.post(URIs.devices, json=request)

    @table_api
    async def fetch_ipaddrs(self, request: dict) -> Response:
        """
        Fetch <Technology | Adressing | Managed IPs> table records.

        Parameters
        ----------
        request: dict
            The API body request payload, prepared by the table_api decorator

        Returns
        -------
        The HTTPx response, which will be post-processed by the table_api decorator.
        """
        default_columns = [
            "sn",
            "snHw",
            "hostname",
            "intName",
            "siteName",
            "mac",
            "ip",
            "net",
        ]

        request.setdefault("columns", default_columns)

        return await self.api.post(URIs.managed_ipaddrs, json=request)

    @table_api
    async def fetch_optics(self, request: dict) -> Response:
        """
        Fetch <Technology | Part numbers | SFP modules> table records.

        Parameters
        ----------
        request: dict
            The API body request payload, prepared by the table_api decorator

        Returns
        -------
        The HTTPx response, which will be post-processed by the table_api decorator.
        """
        filter_report = {"pid": ["color", "eq", COLOR_GREEN]}

        request.setdefault("columns", DEFAULT_PARTS_COLUMNS)
        request["filters"].update(filter_report)
        request["reports"] = "/inventory/part-numbers"

        return await self.api.post(URIs.device_parts, json=request)

    @table_api
    async def fetch_device_parts(self, request: dict) -> Response:
        """
        Fetch <Technology | Part numbers> table records.

        Parameters
        ----------
        request: dict
            The API body request payload, prepared by the table_api decorator

        Returns
        -------
        The HTTPx response, which will be post-processed by the table_api decorator.
        """
        request.setdefault("columns", DEFAULT_PARTS_COLUMNS)
        return await self.api.post(URIs.device_parts, json=request)
