from aioipfabric import IPFabricClient


async def example(**options):

    async with IPFabricClient() as ipf:
        res = await ipf.fetch_devices(**options)
        print(f"There are {len(res)} devices in IP Fabric")
