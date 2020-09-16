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

from typing import Optional, Dict, List
from dataclasses import dataclass

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

    async def fetch_devices(
        self,
        columns: Optional[List[str]] = None,
        filters: Optional[Dict] = None,
        raw=False,
    ) -> dict:
        """
        This coroutine is used to fetch all device inventory records.  The
        complete API response body is returned, including the _meta data.

        Parameters
        ----------
        columns:
            Optional list of table columns to retrieve.  If not provided, then
            all of the table columns are retrieved.

        filters:
            Optional dictionary definiting API filters structure to limit the
            devices retrieved from inventory.

        raw:
            When True the API payload is returned that includes both the _meta and the
            data keys.

            When False (default) only the API data list is returned.
        """
        payload = {
            "columns": columns
            or [
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
                "model",
            ],
            "snapshot": self.active_snapshot,
        }

        if filters:
            payload["filters"] = filters

        res = await self.api.post(URIs.devices, json=payload)
        res.raise_for_status()
        body = res.json()
        return body if raw else body["data"]

    async def fetch_ipaddrs(self, raw=False):
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
        body = res.json()
        return body if raw else body["data"]

    async def fetch_optics(self, raw=False):
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
        body = res.json()
        return body if raw else body["data"]
