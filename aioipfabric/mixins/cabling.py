#  Copyright 2021 Jeremy Schulman
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


@dataclass
class URIs:
    """identifies API URL endpoings used"""

    neighbors = "/tables/neighbors/all"


class IPFCablingMixin(IPFBaseClient):
    @table_api
    async def fetch_cabling(self, request: dict) -> Response:
        """Fetch the CDP/LLDP 'cabling' information"""

        columns = [
            "localHost",
            "localInt",
            "siteName",
            "remoteHost",
            "remoteIp",
            "remoteInt",
        ]

        request.setdefault("columns", columns)
        return await self.api.post(URIs.neighbors, json=request)
