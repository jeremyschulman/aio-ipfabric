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
from functools import cached_property

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from .base_client import IPFBaseClient


# -----------------------------------------------------------------------------
#
#                                 CODE BEGINS
#
# -----------------------------------------------------------------------------


@dataclass
class URIs:
    """ identifies API URL endpoings used"""

    devices = "tables/inventory/devices/"
    device_parts = "tables/inventory/pn"
    managed_ipaddrs = "tables/addressing/managed-devs/"
    snapshots = "snapshots"


class IPFInventoryMixin(IPFBaseClient):
    """
    IP Fabric client mixin supporting the inventory features.
        - devices
        - device optics
        - device managed IP addresses
    """

    @cached_property
    def devices(self):
        """ cache of the existing inventory of devices """
        return self.loop.run_until_complete(self.fetch_devices())["data"]

    @cached_property
    def device_optics(self):
        """ cache of the existing inventory of device parts"""
        return self.loop.run_until_complete(self.fetch_optics())["data"]

    async def fetch_devices(self) -> dict:
        """
        This coroutine is used to fetch all device inventory records.  The
        complete API response body is returned, including the _meta data.
        """
        payload = {
            "columns": [
                "id",
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
            ],
            "snapshot": self.active_snapshot,
        }

        res = await self.api.post(URIs.devices, json=payload)
        res.raise_for_status()
        return res.json()

    async def fetch_ipaddrs(self):
        """ couroutine to retrieve all IP addresses used by all managed devices """
        payload = {
            "columns": [
                "id",
                "sn",
                "hostname",
                "intName",
                "siteName",
                "mac",
                "ip",
                "net",
            ],
            "snapshot": self.active_snapshot,
        }
        res = await self.api.post(URIs.managed_ipaddrs, json=payload)
        res.raise_for_status()
        return res.json()

    async def fetch_optics(self):
        """ coroutine to retrieve all optic parts based on an intent verification rule """
        optic_modules = {
            "columns": [
                "id",
                "deviceSn",
                "hostname",
                "siteKey",
                "siteName",
                "deviceId",
                "name",
                "dscr",
                "pid",
                "sn",
                "vid",
                "vendor",
                "platform",
                "model",
            ],
            "filters": {"pid": ["color", "eq", "0"]},
            "snapshot": self.active_snapshot,
            "reports": "/inventory/part-numbers",
        }
        res = await self.api.post(URIs.device_parts, json=optic_modules)
        res.raise_for_status()
        return res.json()
