from httpx import Response
from aioipfabric import IPFabricClient, table_api
from aioipfabric.mixins.inventory import URIs


@table_api
async def fetch_device_uptime(client, request: dict) -> Response:
    """
    Find any device uptime that is 'out of compliance' meaning it has an intent
    validation value that is not green (> 0).
    """
    filter_report = client.parse_filter("uptime color > 0")
    request["filters"].update(filter_report)
    request["reports"] = "/inventory/devices"
    return await client.api.post(url=URIs.devices, json=request)


async def example(**options):
    """
    Fetch all of the devices with uptime out of compliance.

    Other Parameters
    ----------------
    options: dict
        Request options as allowed for by the table_api decorator.

    Returns
    -------
    By default the list of found records, or empty-list.
    """

    ipf = IPFabricClient()
    await ipf.login()

    columns = [
        "hostname",
        "siteName",
        "uptime",
        "vendor",
        "family",
        "platform",
        "model",
        "version",
    ]

    res = await fetch_device_uptime(ipf, columns=columns, **options)

    await ipf.api.aclose()
    return res
