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

from typing import Optional, Callable, Dict
from asyncio import Semaphore

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
        self,
        since_ts: int,
        factory_filename: Callable[[Dict], str],
        before_ts: Optional[int] = None,
        sanitized: Optional[bool] = False,
        batch_sz: Optional[int] = 1,
    ):
        """
        This coroutine is used to download the latest copy of all devices in the
        active snapshot.

        Parameters
        ----------
        since_ts:
            The timestamp criteria for retrieving configs such that lastChecked
            is >= since_ts. This value is the epoch timestamp * 1_000; which is
            the IP Fabric native storage unit for timestamps.

        factory_filename:
            A function that is used to generate the base device configuration
            filename.  The function is given the device record dictionary that
            contains the fields for host name ('hostname') and serial number
            ('sn').

        before_ts:
            The timestamp criteria for retrieving configs such that lastChecked
            is <= before_ts.  This value is the epoch timestamp * 1_000.

        sanitized:
            Determines if the configuration should be santized as it is extracted
            from the IP Fabric system.

        batch_sz:
            Number of concurrent download tasks; used to rate-limit IPF API
            due to potential performance related issue.

        Notes
        -----
        From experiments with the IP Fabric API, observations are that batch_sz
        must be 1 as higher values result in result text as combinations of
        multiple devices.
        """

        # The first step is to retrieve each of the configuration "hash" records
        # using the active snapshot start timestamp as the basis for the filter.

        if before_ts:
            # TODO: The attempt to use the 'and' with this API call causes an
            #       Error 500 response code.  Leaving this code in for now so we
            #       can debug/troubleshoot with IPF team.

            if before_ts <= since_ts:
                raise ValueError(f"before_ts {before_ts} <= since_ts {since_ts}")

            filters = {
                "and": [
                    {"lastCheck": ["gte", since_ts]},
                    {"lastCheck": ["lte", before_ts]},
                ]
            }
        else:
            filters = {"lastCheck": ["gte", since_ts]}

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
            "sort": {"column": "lastChange", "order": "desc"},
            "reports": "/management/configuration/first",
        }

        res = await self.api.post(URIs.device_config_refs, json=payload)
        res.raise_for_status()
        records = res.json()["data"]

        # NOTE: For unknown reasons, there are devices that have more than one
        # record in this response collection.  Therefore we need to retain only
        # the most recent value using a dict and the setdefault method

        filtered_records = dict()

        for rec in records:
            filtered_records.setdefault(rec["sn"], rec)

        records = list(filtered_records.values())

        # Now we need to retrieve each config file based on each record hash.
        # We will create a list of tasks for this process and run them
        # concurrently in batches (due to API related reasons).

        batching_sem = Semaphore(batch_sz)

        async def fetch_device_config(_hash):
            """ perform a config fetch limited by semaphore """
            async with batching_sem:
                api_res = await self.api.get(
                    URIs.download_device_config,
                    params={"hash": _hash, "sanitized": sanitized},
                    timeout=60,
                )
                return api_res

        fetch_tasks = {fetch_device_config(rec["hash"]): rec for rec in records}

        print(
            f"Downloading {len(fetch_tasks)} device configurations in {batch_sz} batches ... "
        )

        async for task in as_completed(fetch_tasks, timeout=5 * 60):
            coro = task.get_coro()
            rec = fetch_tasks[coro]
            t_result = task.result()

            async with aiofiles.open(factory_filename(rec), "w+") as ofile:
                await ofile.write(t_result.text)
