"""
This file contains the "ipf table ..." command that is used to fetch IP Fabric Table data and
save to file or output to console.
"""

# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

import asyncio
import json

# -----------------------------------------------------------------------------

# Public Imports
# -----------------------------------------------------------------------------

import click
from httpx import HTTPStatusError

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from aioipfabric import IPFabricClient

from .main import cli
from .clihelpers import callback_csv_list


# -----------------------------------------------------------------------------
#
#                                 CODE BEGINS
#
# -----------------------------------------------------------------------------


async def get_table(**options):
    """
    Coroutine used to fetch the data from IP Fabric and either store to file or
    display to console.
    """
    args = dict(url="/tables{options['table']}", columns=options["columns"])

    if (fexpr := options["filter"]) is not None:
        args["filters"] = IPFabricClient.parse_filter(fexpr)

    async with IPFabricClient() as ipf:
        try:
            records = await ipf.fetch_table(**args)

        except HTTPStatusError as exc:
            print(f"{exc.response.text}")
            return

    if (save_file := options["save_file"]) is not None:
        print(f"SAVE: {save_file.name}")
        json.dump(records, save_file, indent=3)
        return

    json.dumps(records, indent=3)


# -----------------------------------------------------------------------------
#
#                                   CLI
#
# -----------------------------------------------------------------------------


@cli.command("table")
@click.option(
    "-t",
    "--table",
    "table",
    help="Table URI following /v1/tables",
    metavar="[/TABLE_URI]",
    required=True,
)
@click.option(
    "-c",
    "--columns",
    required=True,
    help="Table column(s)",
    metavar="[name1,name2,...]",
    multiple=True,
    callback=callback_csv_list,
)
@click.option("-f", "--filter", "filter", help="filter expression")
@click.option(
    "-s", "--save", "save_file", help="save to output JSON file", type=click.File("w+")
)
def cli_table(**options):
    """
    Fetch IP Fabric Table.

    \b
    Example options: to get the contents of the interface connectivty matrix:
    \b
        --table /interfaces/connectivity-matrix
        --columns localHost,localInt,remoteHost,remoteInt
        --filter "and(siteName = nyc1, protocol = cdp)"
        --save nyc1-matrix.json
    """
    asyncio.run(get_table(**options))
