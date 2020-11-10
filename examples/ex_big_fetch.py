import asyncio
from aioipfabric import IPFabricClient

ipf = IPFabricClient()


async def demo():
    tasks = list()
    for count in range(10):
        task = asyncio.create_task(
            ipf.fetch_table(
                url="/tables/inventory/interfaces",
                columns=["hostname", "intName", "siteName"],
                return_as="raw",
            )
        )
        tasks.append(task)

    return await asyncio.gather(*tasks, return_exceptions=True)


async def demo2(url, columns, page_sz=500, timeout=60 * 5):

    res = await ipf.fetch_table(
        url=url, columns=columns, pagination=dict(start=0, limit=1), return_as="meta"
    )

    count = res["count"]
    pages, more = divmod(count, page_sz)
    if more:
        pages += 1

    paginations = [
        dict(start=page_start, limit=page_sz) for page_start in range(0, count, page_sz)
    ]

    tasks = [
        asyncio.create_task(ipf.fetch_table(url=url, columns=columns, pagination=pg))
        for pg in paginations
    ]

    print(f"Fetching {pages} pages ...", flush=True)
    total_records = list()
    for page, next_done in enumerate(asyncio.as_completed(tasks, timeout=timeout)):
        res = await next_done
        print(f"Page {page} of {pages}, got {len(res)} records.")
        total_records.extend(res)

    return total_records


if_table_url = "/tables/inventory/interfaces"
if_table_columns = ["hostname", "intName", "siteName"]

mac_table_url = "/tables/addressing/mac"
mac_table_columns = ["hostname", "intName", "siteName", "mac", "vlan"]
