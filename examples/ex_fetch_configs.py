import maya  # noqa: you need to install maya package in your virtualenv for this demo

from aioipfabric import IPFabricClient
from aioipfabric.mixins.configs import URIs


async def fetch_config(ipf: IPFabricClient, hostname: str):
    res = await ipf.fetch_table(
        url=URIs.device_config_refs,
        columns=["sn", "hostname", "lastChange", "lastCheck", "status", "hash"],
        pagination={"limit": 1},
        sort={"column": "lastCheck", "order": "desc"},
        filters=ipf.parse_filter(f"hostname ~ {hostname}"),
    )

    rec = res[0]

    res = await ipf.api.get(
        url=URIs.download_device_config, params=dict(hash=rec["hash"])
    )
    res.raise_for_status()
    return rec, res.text


async def demo(hostname: str, show_config=False):
    async with IPFabricClient() as ipf:
        rec, config_text = await fetch_config(ipf, hostname)
        change_dt = maya.MayaDT(rec["lastChange"] / 1000)
        check_dt = maya.MayaDT(rec["lastCheck"] / 1000)
        print("Last Changed:", change_dt.slang_date(), ",", change_dt.slang_time())
        print("Last Checked", check_dt.slang_date(), ",", check_dt.slang_time())

        if show_config:
            print(config_text)

        print(rec)
