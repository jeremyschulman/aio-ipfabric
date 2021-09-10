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

from typing import Optional, Callable, Dict, Awaitable, List
from asyncio import Semaphore
from dataclasses import dataclass
import logging

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

import aioipfabric
from aioipfabric.aiofut import as_completed
from aioipfabric.base_client import IPFBaseClient

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = ["IPFConfigsMixin", "URIs"]


# -----------------------------------------------------------------------------
#
#                                 CODE BEGINS
#
# -----------------------------------------------------------------------------

_LOG = logging.getLogger(aioipfabric.__package__)


@dataclass
class URIs:
    """API endpoints"""

    device_config_refs = "tables/management/configuration"
    download_device_config = "tables/management/configuration/download"
    trigger_backup = "discovery/trigger-config-backup"


class IPFConfigsMixin(IPFBaseClient):
    """
    Mixin to support fetching device configurations (text)
    """

    async def fetch_device_configs(
        self,
        on_config: Callable[[Dict, str], Awaitable[None]],
        since_ts: int,
        all_configs: Optional[bool] = False,
        before_ts: Optional[int] = None,
        filters: Optional[Dict] = None,
        device_filter: Optional[Callable[[Dict], bool]] = None,
        sanitized: Optional[bool] = False,
        batch_sz: Optional[int] = 1,
        dry_run: Optional[bool] = False,
    ) -> List[Dict]:
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

        all_configs:
            When False (default) this coroutine will fetech only those
            configurations that have _changed_.  Use all_configs=True when you
            want to fetch the configs regardless if they have changed or not.

        on_config:
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

        device_filter:
            The Caller can optionally provide a function used to filter if the
            provided device-hash record should be used or not to retrieve the
            device configuration.  This parameter is useful for cases where the
            Caller wants to limit the device configuration retrival based on
            filtering beyond the get-hash filter fields of sn and hostname.

        before_ts:
            The timestamp criteria for retrieving configs such that lastChecked
            is <= before_ts.  This value is the epoch timestamp * 1_000.

        sanitized:
            Determines if the configuration should be santized as it is extracted
            from the IP Fabric system.

        batch_sz:
            Number of concurrent download tasks; used to rate-limit IPF API
            due to potential performance related issue.

        dry_run:
            When True this coroutine will return the list of devices
            that would be used to retrieve the configuration files; but
            not actually get the configs.

        Returns
        -------
        List of device-hash records that were used to perform the config file
        fetching process.

        Notes
        -----
        From experiments with the IP Fabric API, v3.6.1, observations are that
        batch_sz must be 1 as higher values result in result text as
        combinations of multiple devices. (Confirmed by IP Fabric engineering
        2020-Sep-09)
        """

        since_criteria = "lastCheck" if all_configs else "lastChange"

        # The first step is to retrieve each of the configuration "hash" records
        # using the active snapshot start timestamp as the basis for the filter.

        if before_ts:
            # TODO: The attempt to use the 'and' with this API call causes an
            #       Error 500 response code.  Leaving this code in for now so we
            #       can debug/troubleshoot with IPF team.

            if before_ts <= since_ts:
                raise ValueError(f"before_ts {before_ts} <= since_ts {since_ts}")

            filters_ = {since_criteria: ["gte", since_ts]}

            # filters_ = {
            #     "and": [
            #         {"lastCheck": ["gte", since_ts]},
            #         {"lastCheck": ["lte", before_ts]},
            #     ]
            # }

        else:
            filters_ = {since_criteria: ["gte", since_ts]}

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
            "sort": {"column": since_criteria, "order": "desc"},
            "reports": "/management/configuration/first",
        }

        res = await self.api.post(URIs.device_config_refs, json=payload)
        res.raise_for_status()
        records = res.json()["data"]

        # NOTE: For unknown reasons, there are devices that have more than one
        # record in this response collection.  Therefore we need to retain only
        # the most recent value using a dict and the setdefault method

        if before_ts:
            records = [rec for rec in records if rec[since_criteria] <= before_ts]

        filtered_records = dict()

        for rec in records:
            filtered_records.setdefault(rec["sn"], rec)

        records = list(filtered_records.values())

        if dry_run is True:
            return records

        # TODO NOTE: API workaournd for v3.6
        # since we cannot use the API for before_ts, we need to perform a post
        # API filtering process now

        # TODO NOTE: API limitation
        # Now we need to retrieve each config file based on each record hash. We
        # will create a list of tasks for this process and run them concurrently
        # in batches (due to API related reasons).

        batching_sem = Semaphore(batch_sz)

        async def fetch_device_config(_hash):
            """perform a config fetch limited by semaphore"""
            async with batching_sem:
                api_res = await self.api.get(
                    URIs.download_device_config,
                    params={"hash": _hash, "sanitized": sanitized},
                    timeout=60,
                )
                return api_res

        # create a lookup dictionary that will map the fetch coroutine to the
        # hash record so that when the coroutine completes we can obtain the
        # source device record; this is needed per the use of the `as_completed`
        # function.

        device_filter = device_filter or (lambda x: True)

        fetch_tasks = {
            fetch_device_config(rec["hash"]): rec
            for rec in records
            if device_filter(rec)
        }

        _LOG.debug(
            f"Fetching {len(fetch_tasks)} device configurations in {batch_sz} batches ... "
        )

        async for task in as_completed(fetch_tasks, timeout=5 * 60):
            # the `task` instance will provide both the config text as a result,
            # and allow use to use the associated coroutine as a lookup so we
            # can obtain the device record associated with the config.

            rec = fetch_tasks[task.get_coro()]
            t_result = task.result()

            # pass the device record and device configuration back to the Caller
            # via the callback coroutine so that they can do what they want; for
            # example save the contents to filesystem.

            await on_config(rec, t_result.text)

        # return only the list of device records that were subject to backup
        # processing.

        return list(fetch_tasks.values())

    async def trigger_backup(self, **options):
        """
        This coroutine will cause IP Fabric to trigger a backup process for the
        given device as specified in `options`.  The Caller can provide either
        the management IP address or serial-number of the device (as obtained
        from the Inventory table!).

        Other Parameters
        ----------
        ip: str - The device management IP address
        sn: str - The device serial-number

        Returns
        -------
        None - there is no payload response to the trigger action.

        Raises
        ------
        httpx.Exception
        """
        res = await self.api.post(URIs.trigger_backup, json=options)
        res.raise_for_status()
