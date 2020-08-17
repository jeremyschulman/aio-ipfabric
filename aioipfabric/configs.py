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


class IPFConfigsMixin(IPFBaseClient):
    async def fetch_device_config(
        self, hostname, *domains, sanitized=False, with_body=False
    ):

        # Find the device configuration record; we only want the most recent
        # configuraiton.

        find = (hostname, *(f"{hostname}.{domain}" for domain in domains))

        for each in find:
            filters = {"hostname": ["like", each]}
            payload = {
                "columns": [
                    "_id",
                    "sn",
                    "hostname",
                    "lastChange",
                    "lastCheck",
                    "status",
                    "hash",
                ],
                "filters": filters,
                "snapshot": "$last",
                "pagination": {"limit": 1, "start": 0},
                "sort": {"column": "lastChange", "order": "desc"},
                "reports": "/management/configuration/first",
            }

            res = await self.api.post(URIs.device_config_refs, json=payload)
            res.raise_for_status()
            body = res.json()
            if body["_meta"]["count"] != 0:
                break

        else:
            return None

        # obtain the actual configuration text

        rec = body["data"][0]
        file_hash = rec["hash"]
        params = {"hash": file_hash, "sanitized": sanitized}
        res = await self.api.get(URIs.download_device_config, params=params)
        res.raise_for_status()

        if with_body:
            return res.text, body

        return res.text
