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

from .base_client import IPFBaseClient
from .consts import URIs


class IPFInventoryMixin(IPFBaseClient):
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
            "snapshot": "$last",
        }

        res = await self.api.post(URIs.devices, json=payload)
        res.raise_for_status()
        return res.json()

    async def fetch_ipaddrs(self):
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
            "snapshot": "$last",
        }
        res = await self.api.post(URIs.managed_ipaddrs, json=payload)
        res.raise_for_status()
        return res.json()
