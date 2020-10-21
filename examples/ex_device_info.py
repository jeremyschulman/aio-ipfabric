"""
This example illustrates the process to gather multiple aspects of a device, for example:
    * the device inventory record
    * the device interfaces records
    * the VLANs associated with the device
    * the managed IP addresses associated with the device
"""

from aioipfabric import IPFabricClient, table_api
from aioipfabric.consts import TableFields
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


async def device_info(hostname: str, **api_options):

    async with IPFabricClient() as ipf:

        filter_hostname = IPFabricClient.parse_filter(f"hostname = {hostname}")

        inventory_task = ipf.fetch_devices(filters=filter_hostname, **api_options)
        parts_task = ipf.fetch_device_parts(filters=filter_hostname, **api_options)
        interfaces_task = fetch_device_interfaces(
            ipf, filters=filter_hostname, **api_options
        )
        vlans_task = fetch_device_vlans(ipf, filters=filter_hostname, **api_options)
        ipaddrs_task = fetch_device_ipaddrs(ipf, filters=filter_hostname, **api_options)

        results = await asyncio.gather(
            inventory_task,
            parts_task,
            interfaces_task,
            vlans_task,
            ipaddrs_task,
            return_exceptions=True,
        )

    return results
