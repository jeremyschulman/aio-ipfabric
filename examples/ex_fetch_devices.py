from aioipfabric import IPFabricClient


async def example(site, **options):
    ipf = IPFabricClient()
    await ipf.login()
    return await ipf.fetch_devices(
        filters=ipf.parse_filter(f"siteName = {site}"), **options
    )
