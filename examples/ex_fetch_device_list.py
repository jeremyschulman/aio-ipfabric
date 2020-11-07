#!/usr/bin/env python

import sys
from pathlib import Path
from aioipfabric import IPFabricClient
import asyncio
from operator import itemgetter
from tabulate import tabulate  # noqa: you must install tabulate in your virtualenv


loop = asyncio.get_event_loop()


async def run(ipf: IPFabricClient, device_list, callback):
    def _done(_task: asyncio.Task):
        _host = _task.get_name()
        _res = _task.result()
        if not len(_res):
            print(f"IPF device not found: {_host}")
            return

        callback(_host, _res[0])

    tasks = {
        [
            (
                task := loop.create_task(
                    ipf.fetch_devices(filters=ipf.parse_filter(f"hostname ~ '{host}'")),
                    name=host,
                )
            ),
            task.add_done_callback(_done),
        ][0]
        for host in device_list
    }

    await asyncio.gather(*tasks)


async def demo(filename):

    if not (fp := Path(filename)).is_file():
        sys.exit(f"File does not exist: {filename}")

    device_list = fp.read_text().splitlines()

    fields = ("hostname", "family", "version", "model")
    get_fields = itemgetter(*fields)
    results = list()

    def callback(name, rec):
        print(f"Adding {name}")
        results.append(get_fields(rec))

    async with IPFabricClient() as ipf:
        await run(ipf, device_list, callback=callback)

    print(tabulate(headers=fields, tabular_data=sorted(results, key=itemgetter(1, 2))))
