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

from typing import Optional, Callable, Dict, Awaitable
from asyncio import Semaphore
from dataclasses import dataclass
import logging

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

import aioipfabric
from .aiofut import as_completed
from .base_client import IPFBaseClient

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = ["IPFConfigsMixin"]


# -----------------------------------------------------------------------------
#
#                                 CODE BEGINS
#
# -----------------------------------------------------------------------------

_LOG = logging.getLogger(aioipfabric.__package__)


@dataclass
class URIs:
    """ API endpoints """

    device_config_refs = "tables/management/configuration"
    download_device_config = "tables/management/configuration/download"


class IPFConfigsMixin(IPFBaseClient):
    """
    Mixin to support fetching device configurations (text)
    """

    async def fetch_device_configs(
        self,
        callback: Callable[[Dict, str], Awaitable[None]],
        since_ts: int,
        before_ts: Optional[int] = None,
        filters: Optional[Dict] = None,
        sanitized: Optional[bool] = False,
        batch_sz: Optional[int] = 1,
    ):
        """
        This coroutine is used to download the latest copy of devices in the
        active snapshot.  The default behavior is to locate the lastest device
        configuration since the `since_ts` time for all devices.

        If the Caller needs to "go back in time" then both the `since_ts` and
        `before_ts` values should be used and only devices that match:

                since_ts <= lastChange <= before_ts

        If the Caller would like to further filter records based on 'hostname',
        'sn' (serial-number), those filters can be provided in the `filters`
        parameter.

        Parameters
        ----------
        since_ts:
            The timestamp criteria for retrieving configs such that lastChecked
            is >= since_ts. This value is the epoch timestamp * 1_000; which is
            the IP Fabric native storage unit for timestamps.

        callback:
            A coroutine that will be invoked with the device record and
            configuration file content that allows the Caller to do
            something with the content such as save it to a file.

        filters:
            Any additional Caller provided API filters that should be applied in
            addition to using the `since_ts` and `before_ts` options.  This
            filters dictionary allows the caller to be more specific, for
            example regex of hostnames.  The filters only apply to the fields to
            extact the backup record hashs; which primarily include ['sn',
            'hostname', 'status']

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
        From experiments with the IP Fabric API, v3.6.1, observations are that
        batch_sz must be 1 as higher values result in result text as
        combinations of multiple devices. (Confirmed by IP Fabric engineering
        2020-Sep-09)
        """

        # The first step is to retrieve each of the configuration "hash" records
        # using the active snapshot start timestamp as the basis for the filter.

        if before_ts:
            # TODO: The attempt to use the 'and' with this API call causes an
            #       Error 500 response code.  Leaving this code in for now so we
            #       can debug/troubleshoot with IPF team.

            if before_ts <= since_ts:
                raise ValueError(f"before_ts {before_ts} <= since_ts {since_ts}")

            filters_ = {"lastChange": ["gte", since_ts]}

            # filters_ = {
            #     "and": [
            #         {"lastCheck": ["gte", since_ts]},
            #         {"lastCheck": ["lte", before_ts]},
            #     ]
            # }

        else:
            filters_ = {"lastCheck": ["gte", since_ts]}

        # if the Caller provided additional filters, add them now.

        if filters:
            filters_.update(filters)

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
            "filters": filters_,
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

        # since we cannot use the API for before_ts, we need to perform a post
        # API filtering process now

        if before_ts:
            records = [rec for rec in records if rec["lastChange"] <= before_ts]

        # Now we need to retrieve each config file based on each record hash. We
        # will create a list of tasks for this process and run them concurrently
        # in batches (due to API related reasons).

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

        _LOG.debug(
            f"Fetching {len(fetch_tasks)} device configurations in {batch_sz} batches ... "
        )

        async for task in as_completed(fetch_tasks, timeout=5 * 60):
            coro = task.get_coro()
            rec = fetch_tasks[coro]
            t_result = task.result()

            await callback(rec, t_result.text)
