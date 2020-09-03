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

from typing import Optional
from pathlib import Path

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------

import aiofiles

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from .aiofut import as_completed
from .base_client import IPFBaseClient
from .consts import URIs

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = ["IPFConfigsMixin"]


# -----------------------------------------------------------------------------
#
#                                 CODE BEGINS
#
# -----------------------------------------------------------------------------


class IPFConfigsMixin(IPFBaseClient):
    """
    Mixin to support fetching device configurations (text)
    """

    async def fetch_device_config(
        self,
        hostname,
        *domains,
        exact_match: Optional[bool] = False,
        sanitized=False,
        with_body=False,
    ):
        """
        This coroutine is used to return the most recent device
        configuration (text) for the `hostname` provided.

        Parameters
        ----------
        hostname: str
            The device hostname to find.  By default the call to the API will
            use the `like` filter so that you do not need to provide an exact
            match. That said, be careful with the hostname value as it may
            result in a config content response to the wrong hostname.  If you
            want an exact match, set `exact_match` to True

        exact_match: Optional[bool]
            When True will invoke the API with the filter "eq" so that the
            hostname value must be an exact match.

        domains: Optional[List]
            Any domain names that need to be used to find the hostname
            within the inventory

        sanitized: Optional[bool]
            When True will use the IP Fabric sanitize feature to redanct
            sensitive information from the configuration content.

        with_body: Optional[bool]
            When True will return the entire API response body.  By
            default only the configuration content is returned.

        Returns
        -------
        None:
            When the `hostname` is not found in inventory

        device configuration: str
            When `with_body` is False (default)

        API response body: dict
            When `with_body` is True
        """
        # Find the device configuration record; we only want the most recent
        # configuraiton.

        find = (hostname, *(f"{hostname}.{domain}" for domain in domains))
        match_op = "eq" if exact_match else "like"

        for each in find:
            filters = {"hostname": [match_op, each]}
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
                "snapshot": self.active_snapshot,
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
            # if no match found return None
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

    async def download_all_device_configs(
        self, dest_dir: str, sanitized: Optional[bool] = False,
    ):
        """
        This coroutine is used to download the latest copy of all devices in the
        active snapshot.

        Parameters
        ----------
        dest_dir:
            The filepath to an existing directory.  The configuration files
            will be stored into this directory.

        sanitized:
            Determines if the configuration should be santized as it is extracted
            from the IP Fabric system.
        """

        # The first step is to retrieve each of the configuration "hash" records
        # using the active snapshot start timestamp as the basis for the filter.

        dir_obj = Path(dest_dir)
        if not dir_obj.is_dir():
            raise RuntimeError(f"{dest_dir} is not a directory")

        snap_rec = next(
            rec for rec in self.snapshots if rec["id"] == self.active_snapshot
        )

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
            "filters": {"lastCheck": ["gte", snap_rec["tsStart"]]},
            "snapshot": self.active_snapshot,
            "sort": {"column": "lastChange", "order": "desc"},
            "reports": "/management/configuration/first",
        }

        res = await self.api.post(URIs.device_config_refs, json=payload)
        res.raise_for_status()
        records = res.json()["data"]

        # Now we need to retrieve each config file based on each record hash.  We will create
        # a list of tasks for this process and run them all concurrently.

        fetch_tasks = {
            self.api.get(
                URIs.download_device_config,
                params={"hash": rec["hash"], "sanitized": sanitized},
                timeout=60,
            ): rec
            for rec in records
        }

        print(f"Downloading {len(fetch_tasks)} device configurations ... ")
        async for task in as_completed(fetch_tasks, timeout=5 * 60):
            coro = task.get_coro()
            rec = fetch_tasks[coro]

            cfg_file = dir_obj.joinpath(rec["hostname"] + ".cfg")
            print(cfg_file.name)

            res = task.result()
            async with aiofiles.open(cfg_file, "w+") as ofile:
                await ofile.write(res.text)
