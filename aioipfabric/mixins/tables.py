#  Copyright 2020 Julien Manteau
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

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from aioipfabric.base_client import IPFBaseClient

# -----------------------------------------------------------------------------
#
#                                 CODE BEGINS
#
# -----------------------------------------------------------------------------


class IPFTablesMixin(IPFBaseClient):
    """
    IP Fabric client mixin supporting all IPF tables without any preconceptions.
    Dedicated Mixin for specific usecases can be a better fit. 
    """

    async def fetch_table(
        self,
        resourcepath: str,
        columns: [List[str]],
        filters: Optional[Dict] = None,
        raw=False,
    ) -> dict:
        """
        This coroutine is used to fetch all records of the indicated resource path.  The
        complete API response body is returned, including the _meta data.

        Parameters
        ----------
        columns:
            List of table columns to retrieve. Is mandatory (found in IPFabric table help).

        filters:
            Optional dictionary definiting API filters structure to limit the
            devices retrieved from inventory.

        raw:
            When True the API payload is returned that includes both the _meta and the
            data keys.

            When False (default) only the API data list is returned.
        """
        payload = {
            "columns": columns,
            "snapshot": self.active_snapshot,
        }

        if filters:
            payload["filters"] = filters

        res = await self.api.post(resourcepath, json=payload)
        res.raise_for_status()
        body = res.json()
        return body if raw else body["data"]
