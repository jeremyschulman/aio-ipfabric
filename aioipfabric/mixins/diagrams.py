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
from json import dumps

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

    end_to_end_path = "graphs"


class IPFDiagramE2EMixin(IPFBaseClient):
    """Mixin for End-to-End Path query"""

    async def end_to_end_path(
        self,
        src_ip: str,
        dst_ip: Optional[str] = "0.0.0.0",
        proto: Optional[str] = "tcp",
        src_port: Optional[Union[str, int]] = 10000,
        dst_port: Optional[Union[str, int]] = 80,
        sec_drop: Optional[bool] = True,
        lookup: Optional[str] = "unicast",
        grouping: Optional[str] = "siteName"

    ) -> Dict:
        """
        Execute an "End-to-End Path" diagram query for the given set of parameters.

        Parameters
        ----------
        src_ip
            Source IP address or subnet
        dst_ip
            Destination IP address or subnet
        proto
            Protocol: "tcp", "udp", or "icmp"
        src_port
            Source Port
        dst_port
            Destination Port
        sec_drop
            True specifies Security Rules will Drop and not Continue
        lookup
            Type of lookup: "unicast", "multicast", "hostToDefaultGW"
        grouping
            Group by "siteName", "routingDomain", "stpDomain"


        Returns
        -------
        Returns a dictionary with 'graphResult' and 'pathlookup' primary keys.  For more details refer to this
        IPF blog: https://ipfabric.io/blog/end-to-end-path-simulation-with-api/
        """
        res = await self.api.post(
            URIs.end_to_end_path,
            json=dict(
                parameters=dict(
                    startingPoint=src_ip,
                    startingPort=src_port,
                    destinationPoint=dst_ip,
                    destinationPort=dst_port,
                    protocol=proto,
                    type="pathLookup",
                    networkMode=self.network_mode(src_ip, dst_ip),
                    securedPath=sec_drop,
                    pathLookupType=lookup,
                    groupBy=grouping
                ),
                snapshot=self.active_snapshot
            )
        )
        res.raise_for_status()
        return res.json()

    @staticmethod
    def network_mode(src_ip,  dst_ip):
        if '/' in src_ip or '/' in dst_ip:
            return True
        else:
            return False
