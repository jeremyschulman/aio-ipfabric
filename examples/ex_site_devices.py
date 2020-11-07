"""
This example illustrates the process to gather multiple aspects of a device, for example:
    * the device inventory record
    * the device interfaces records
    * the VLANs associated with the device
    * the managed IP addresses associated with the device
"""

from typing import List, Coroutine, Dict
from aioipfabric import IPFabricClient, table_api
from aioipfabric.consts import TableFields
from aioipfabric.mixins.inventory import URIs
import asyncio

from httpx import Response

EXMAPLE_HOSTNAME = "L77R7-LEAF1"


@table_api
async def fetch_device_interfaces(ipf, request: dict) -> Response:
    request[TableFields.columns] = [
        "intName",
        "siteName",
        "l1",
        "l2",
        "reason",
        "dscr",
        "mac",
        "duplex",
        "speed",
        "media",
        "errDisabled",
        "mtu",
        "primaryIp",
    ]

    return await ipf.api.post(url="/tables/inventory/interfaces", json=request)


@table_api
async def fetch_device_vlans(ipf, request: dict) -> Response:
    request[TableFields.columns] = [
        "hostname",
        "siteName",
        "stpDomain",
        "vlanName",
        "vlanId",
        "status",
        "stdStatus",
    ]
    return await ipf.api.post("/tables/vlan/device", json=request)


@table_api
async def fetch_device_ipaddrs(ipf, request: dict) -> Response:
    url = "/tables/addressing/managed-devs"

    request[TableFields.columns] = [
        "intName",
        "dnsName",
        "dnsHostnameMatch",
        "vlanId",
        "dnsReverseMatch",
        "mac",
        "ip",
        "net",
        "type",
        "vrf",
    ]

    return await ipf.api.post(url, json=request)


def device_info(ipf: IPFabricClient, hostname: str, **api_options) -> Coroutine:
    """
    This function returns a coroutine that is responsible for obtaining device
    information for a given `hostname` and returns a dictionary of data representing
    each aspect of the device:
        hostname: the device hostname
        facts: the device inventory record
        parts: the device parts records
        interfaces: the device interface records
        vlans: the vlan used by this device
        ipaddrs: the IP addresses assigned to the device

    Parameters
    ----------
    ipf: IPFabricClient
    hostname: device hostname
    api_options:

    Returns
    -------
    Coroutine, when awaited will return the dictionary as described.
    """
    filter_hostname = IPFabricClient.parse_filter(f"hostname = {hostname}")

    fut = asyncio.gather(
        ipf.fetch_devices(filters=filter_hostname, **api_options),
        ipf.fetch_device_parts(filters=filter_hostname, **api_options),
        fetch_device_interfaces(ipf, filters=filter_hostname, **api_options),
        fetch_device_vlans(ipf, filters=filter_hostname, **api_options),
        fetch_device_ipaddrs(ipf, filters=filter_hostname, **api_options),
        return_exceptions=True,
    )

    async def gather_result():
        res = await fut
        facts = res[0][0]
        return {
            "hostname": facts["hostname"],
            "facts": facts,
            "parts": res[1],
            "interfaces": res[2],
            "vlans": res[3],
            "ipaddrs": res[4],
        }

    return gather_result()


async def fetch_site_devices(ipf: IPFabricClient, site: str) -> List:
    """ return a list of hostnames in the give site """
    request = {
        TableFields.snapshot: ipf.active_snapshot,
        TableFields.columns: ["hostname"],
        TableFields.filters: ipf.parse_filter(f"siteName = {site}"),
    }
    res = await ipf.api.post(url=URIs.devices, json=request)
    res.raise_for_status()
    return [rec["hostname"] for rec in res.json()["data"]]


async def demo(site) -> List[Dict]:
    async with IPFabricClient() as ipf:
        hosts = await fetch_site_devices(ipf, site)

        # create a coroutine for each of the device information fetches
        tasks = [device_info(ipf, host) for host in hosts]

        # run all device fetches concurrently and return the list of dicts
        return await asyncio.gather(*tasks)
