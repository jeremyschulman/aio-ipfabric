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

import ipaddress
from typing import Optional, Union
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

    json_path = "graphs"
    svg_path = "graphs/svg"


class IPFDiagramPathMixin(IPFBaseClient):
    """
    Mixin for Path Lookup queries.
    After initializing you can set SVG to True to return SVG object instead of JSON data

    References
    ----------
    For more details refer to this feature, see IPF blog:
    https://ipfabric.io/blog/end-to-end-path-simulation-with-api/

    "Region" support added in v5:
    https://docs.ipfabric.io/main/releases/release_notes/5.0/
    """

    svg: bool = False

    async def path_unicast_lookup(
        self,
        src_ip: str,
        dst_ip: str,
        proto: str = "tcp",
        src_port: Optional[int] = 10000,
        dst_port: Optional[int] = 80,
        sec_drop: Optional[bool] = True,
        grouping: Optional[str] = "siteName",
        flags: Optional[list] = None,
        **opt_args,
    ) -> Union[dict, bytes]:
        """
        Execute an "End-to-End Path" diagram query for the given set of parameters.

        Parameters
        ----------
        src_ip
            Source IP address or subnet
        dst_ip
            Destination IP address/subnet, or multicast group
        proto
            Protocol: "tcp", "udp", or "icmp"
        src_port
            Source Port for tcp or udp
        dst_port
            Destination Port for tcp or udp
        sec_drop
            True specifies Security Rules will Drop packets and not Continue
        grouping
            Group by "siteName", "routingDomain", "stpDomain"
        flags
            TCP flags, defaults to None. Must be a list and only allowed values
            can be subet of ['ack', 'fin', 'psh', 'rst', 'syn', 'urg']

        Other Parameters
        ----------------
        As of IPF v5 there are additional parameters for use with "regions".  Refer to the
        documentation, and use those parameter names as-is and as described.

        Returns
        -------
        E2E object json contains a dictionary with 'graphResult' and 'pathlookup' primary keys.
        If SVG set to True E2E.svg will contain bytes data of SVG image you can write to a file or process in webpage.

        For more details refer to this IPF blog: https://ipfabric.io/blog/end-to-end-path-simulation-with-api/
        """
        parameters = dict(
            startingPoint=src_ip,
            startingPort=src_port,
            destinationPoint=dst_ip,
            destinationPort=dst_port,
            protocol=proto,
            type="pathLookup",
            securedPath=sec_drop,
            pathLookupType="unicast",
            groupBy=grouping,
            networkMode=self.check_subnets(src_ip, dst_ip),
            **opt_args,
        )
        parameters = self.check_proto(parameters, flags)

        return await self.submit_query(parameters)

    async def path_multicast_lookup(
        self,
        src_ip: str,
        grp_ip: str,
        proto: str = "tcp",
        rec_ip: Optional[str] = None,
        src_port: Optional[int] = 10000,
        dst_port: Optional[int] = 80,
        sec_drop: Optional[bool] = True,
        grouping: Optional[str] = "siteName",
        flags: Optional[list] = None,
        **opt_args,
    ) -> Union[dict, bytes]:
        """
        Execute an "End-to-End Path" diagram query for the given set of parameters.

        Parameters
        ----------
        src_ip
            Source IP address
        grp_ip
            Multicast group IP Address
        rec_ip
            Optional: Receiver IP
        proto
            Protocol: "tcp", "udp", or "icmp"
        src_port
            Source Port for tcp or udp
        dst_port
            Destination Port for tcp or udp
        sec_drop
            True specifies Security Rules will Drop packets and not Continue
        grouping
            Group by "siteName", "routingDomain", "stpDomain"
        flags
            TCP flags, defaults to None. Must be a list and only allowed values
            can be subet of ['ack', 'fin', 'psh', 'rst', 'syn', 'urg']

        Other Parameters
        ----------------
        As of IPF v5 there are additional parameters for use with "regions".  Refer to the
        documentation, and use those parameter names as-is and as described.

        Returns
        -------
        E2E object json contains a dictionary with 'graphResult' and
        'pathlookup' primary keys. If SVG set to True E2E.svg will contain
        bytes data of SVG image you can write to a file or process in webpage.
        """
        if self.check_subnets(src_ip, grp_ip):
            raise SyntaxError(
                "Multicast does not support subnets, please provide a single IP for Source and Group"
            )

        parameters = dict(
            source=src_ip,
            sourcePort=src_port,
            group=grp_ip,
            groupPort=dst_port,
            protocol=proto,
            type="pathLookup",
            securedPath=sec_drop,
            pathLookupType="multicast",
            groupBy=grouping,
            **opt_args,
        )

        if rec_ip:
            if self.check_subnets(rec_ip):
                raise SyntaxError(
                    "Multicast Receiver IP must be a single IP not subnet."
                )
            else:
                parameters["receiver"] = rec_ip

        parameters = self.check_proto(parameters, flags)

        return await self.submit_query(parameters)

    async def path_host_to_gateway(
        self, src_ip: str, grouping: Optional[str] = "siteName"
    ) -> Union[dict, bytes]:
        """
        Execute a "Host to Gateway" diagram query for the given set of parameters.

        Parameters
        ----------
        src_ip
            Source IP address or subnet
        grouping
            Group by "siteName", "routingDomain", "stpDomain"

        Returns
        -------
        E2E object json contains a dictionary with 'graphResult' and
        'pathlookup' primary keys. If SVG set to True E2E.svg will contain
        bytes data of SVG image you can write to a file or process in webpage.
        """
        self.check_subnets(src_ip)
        parameters = dict(
            startingPoint=src_ip,
            type="pathLookup",
            pathLookupType="hostToDefaultGW",
            groupBy=grouping,
        )
        return await self.submit_query(parameters)

    async def submit_query(self, parameters) -> Union[dict, bytes]:
        """
        Submits query to the API

        Parameters
        ----------
        parameters
            dict: Data to submit

        Returns
        -------
        Dictionary if JSON or Bytes if SVG
        """
        data = dict(parameters=parameters, snapshot=self.active_snapshot)
        api = URIs.json_path if self.svg is False else URIs.svg_path
        res = await self.api.post(api, json=data)
        res.raise_for_status()
        if self.svg:
            return res.content
        else:
            return res.json()

    @staticmethod
    def check_proto(parameters, flags) -> dict:
        """
        Checks parameters and flags

        Parameters
        ----------
        parameters
            dict: Data to Post
        flags
            list: List of opptional TCP flags

        Returns
        -------
        dict: formatted parameters, removing ports if icmp
        """
        if parameters["protocol"] == "tcp" and flags:
            if all(x in ["ack", "fin", "psh", "rst", "syn", "urg"] for x in flags):
                parameters["flags"] = flags
            else:
                raise SyntaxError(
                    "Only accepted TCP flags are ['ack', 'fin', 'psh', 'rst', 'syn', 'urg']"
                )
        elif parameters["protocol"] == "icmp":
            parameters.pop("startingPort", None)
            parameters.pop("destinationPort", None)
            parameters.pop("sourcePort", None)
            parameters.pop("groupPort", None)
        return parameters

    @staticmethod
    def check_subnets(*ips) -> bool:
        """
        Checks for valid IP Addresses or Subnet

        Parameters
        ----------
        *ips
            ip addresses

        Returns
        -------
        True if a subnet is found to set to networkMode, False if only hosts
        """
        masks = set()
        for ip in ips:
            try:
                masks.add(ipaddress.IPv4Interface(ip).network.prefixlen)
            except (ipaddress.AddressValueError, ipaddress.NetmaskValueError):
                raise ipaddress.AddressValueError(f"{ip} is not a valid IP or subnet.")

        return True if masks != {32} else False
