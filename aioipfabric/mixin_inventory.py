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

from .base_client import IPFBaseClient, table_api
from .consts import COLOR_GREEN

# -----------------------------------------------------------------------------
#
#                                 CODE BEGINS
#
# -----------------------------------------------------------------------------


@dataclass
class URIs:
    """ identifies API URL endpoings used"""

    devices = "/tables/inventory/devices/"
    device_parts = "/tables/inventory/pn"
    managed_ipaddrs = "/tables/addressing/managed-devs/"
    snapshots = "/snapshots"


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
            "hostname",
            "siteKey",
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
        request.setdefault("columns", default_columns)
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
        default_columns = ["sn", "hostname", "intName", "siteName", "mac", "ip", "net"]

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

        default_columns = [
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

        request.setdefault("columns", default_columns)
        request["filters"].update(filter_report)
        request["reports"] = "/inventory/part-numbers"

        return await self.api.post(URIs.device_parts, json=request)
