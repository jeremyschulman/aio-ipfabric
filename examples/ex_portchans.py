from aioipfabric import IPFabricClient as _IPFClient
from aioipfabric.mixins.portchan import IPFPortChannels


class IPFabricClient(_IPFClient, IPFPortChannels):
    pass


ipf = IPFabricClient()


async def demo(**params):
    if (filters := params.pop("filters", None)) is not None:
        params["filters"] = ipf.parse_filter(filters)

    res = await ipf.fetch_portchannels(**params)
    return res
