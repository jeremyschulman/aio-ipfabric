import asyncio
from aioipfabric import IPFabricClient
from aioipfabric.mixins.diagrams import IPFDiagramE2EMixin


class Client(IPFabricClient, IPFDiagramE2EMixin):
    pass


asyncio.set_event_loop(asyncio.get_event_loop())


async def end_to_end(**options):
    async with Client() as ipf:
        return await ipf.end_to_end_path(**options)
