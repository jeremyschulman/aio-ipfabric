import asyncio
from aioipfabric import IPFabricClient
from aioipfabric.mixins.configs import IPFConfigsMixin


class Client(IPFabricClient, IPFConfigsMixin):
    pass


asyncio.set_event_loop(asyncio.get_event_loop())


async def backup_device(**options):
    async with Client() as ipf:
        return await ipf.trigger_backup(**options)
