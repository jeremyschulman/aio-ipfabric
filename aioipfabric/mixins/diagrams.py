#  Copyright 2020 Jeremy Schulman
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
"""
This module contains IPF client mixins that perform the "diagram" queries.
"""

# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

from typing import Optional, Dict, Union
from dataclasses import dataclass

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from aioipfabric.base_client import IPFBaseClient


# -----------------------------------------------------------------------------
#
#                                 CODE BEGINS
#
# -----------------------------------------------------------------------------


@dataclass
class URIs:
    """identifies API URL endpoints used"""

    end_to_end_path = "graph/end-to-end-path"


class IPFDiagramE2EMixin(IPFBaseClient):
    """Mixin for End-to-End Path query"""

    async def end_to_end_path(
        self,
        src_ip: str,
        dst_ip: Optional[str] = "0.0.0.0",
        proto: Optional[str] = "tcp",
        src_port: Optional[Union[str, int]] = 10_000,
        dst_port: Optional[Union[str, int]] = 10_000,
        check_rpf: Optional[bool] = True,
        check_asymmetric: Optional[bool] = False,
    ) -> Dict:
        """
        Execute an "End-to-End Path" diagram query for the given set of parameters.

        Parameters
        ----------
        src_ip
            Source IP address
        dst_ip
            Destination IP address
        proto
            Protocol: "tcp", "udp", or "icmp"
        src_port
            Source Port
        dst_port
            Destination Port
        check_rpf
            Boolean to check for reverse path forwarding
        check_asymmetric
            Boolean to check for asymmetric routine

        Returns
        -------
        Returns a dictionary with 'graph' and 'ad' primary keys.  For more details refer to this
        IPF blog: https://ipfabric.io/blog/end-to-end-path-simulation-with-api/
        """
        res = await self.api.get(
            URIs.end_to_end_path,
            params=dict(
                source=src_ip,
                sourcePort=src_port,
                destination=dst_ip,
                destinationPort=dst_port,
                protocol=proto,
                asymmetric=check_asymmetric,
                rpf=check_rpf,
                snapshot=self.active_snapshot,
            ),
        )
        res.raise_for_status()
        return res.json()
