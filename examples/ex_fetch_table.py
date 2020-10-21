from aioipfabric import IPFabricClient


async def example(site, **options):
    async with IPFabricClient() as ipf:
        return await ipf.fetch_table(
            url="/tables/inventory/devices",
            filters=ipf.parse_filter(f"siteName = {site}"),
            columns=["hostname", "loginIp"],
            **options,
        )
