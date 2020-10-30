#!/usr/bin/env python

import sys
from pathlib import Path
from aioipfabric import IPFabricClient
import asyncio
from operator import itemgetter
from tabulate import tabulate


loop = asyncio.get_event_loop()


async def run(ipf: IPFabricClient, device_list, callback):
    def _done(_task):
        _host = _task.get_name()
        _res = _task.result()
        if not len(_res):
            print(f"IPF device not found: {_host}")
            return

        callback(_res[0])

    tasks = [
        (
            task := loop.create_task(
                ipf.fetch_devices(filters=ipf.parse_filter(f"hostname ~ '{host}'")),
                name=host,
            )
        )
        and task.add_done_callback(_done)
        or task
        for host in device_list
    ]

    await asyncio.gather(*tasks)


async def demo(filename):

    try:
        device_list = Path(filename)
        if not device_list.is_file():
            sys.exit(f"File does not exist: {filename}")
    except KeyError:
        sys.exit("Missing filename argument")

    device_list = device_list.read_text().splitlines()

    fields = ("hostname", "family", "version", "model")
    get_fields = itemgetter(*fields)
    results = list()

    async with IPFabricClient() as ipf:
        await run(
            ipf, device_list, callback=lambda rec: results.append(get_fields(rec))
        )

    print(tabulate(headers=fields, tabular_data=sorted(results, key=itemgetter(1, 2))))
