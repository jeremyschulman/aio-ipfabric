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
from typing import Optional, Dict
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

    end_to_end_path = "graphs"


class IPFDiagramE2EMixin(IPFBaseClient):
    """Mixin for End-to-End Path query"""

    def end_to_end_path(
        self,
        src_ip: str,
        dst_ip: Optional[str] = "0.0.0.0",
        proto: Optional[str] = "tcp",
        src_port: Optional[int] = 10000,
        dst_port: Optional[int] = 80,
        sec_drop: Optional[bool] = True,
        lookup: Optional[str] = "unicast",
        grouping: Optional[str] = "siteName",
        flags: Optional[list] = list()
    ) -> Dict:
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
        lookup
            Type of lookup: "unicast" or "multicast"
        grouping
            Group by "siteName", "routingDomain", "stpDomain"
        flags
            TCP flags, defaults to None. Must be a list and only allowed values can be subet of ['ack', 'fin', 'psh', 'rst', 'syn', 'urg']


        Returns
        -------
        Returns a dictionary with 'graphResult' and 'pathlookup' primary keys.  For more details refer to this
        IPF blog: https://ipfabric.io/blog/end-to-end-path-simulation-with-api/
        """
        
        parameters = dict(
            startingPoint=src_ip,
            startingPort=src_port,
            destinationPoint=dst_ip,
            destinationPort=dst_port,
            protocol=proto,
            type="pathLookup",
            securedPath=sec_drop,
            pathLookupType=lookup,
            groupBy=grouping
        )

        parameters = self.check_ips(parameters)
        parameters = self.tcp_flags(parameters, flags)

        if proto == 'icmp':
            del parameters['destinationPort'], parameters['startingPort']
        if lookup == 'multicast':
            del parameters['networkMode']
            parameters['source'] = parameters.pop('startingPoint')
            parameters['group'] = parameters.pop('destinationPoint')
            if proto != 'icmp':
                parameters['sourcePort'] = parameters.pop('startingPoint')
                parameters['groupPort'] = parameters.pop('destinationPoint')
            if '/' in parameters['source'] or '/' in parameters['group']:
                raise SyntaxError("Multicast lookups only accept single IP's not subnets.")

        return self.submit_query(parameters)

    def host_to_gateway(
        self,
        src_ip: str,
        grouping: Optional[str] = "siteName",
    ) -> Dict:
        """
        Execute an "Host to Gateway" diagram query for the given set of parameters.

        Parameters
        ----------
        src_ip
            Source IP address or subnet
        grouping
            Group by "siteName", "routingDomain", "stpDomain"


        Returns
        -------
        Returns a dictionary with 'graphResult' and 'pathlookup' primary keys.  For more details refer to this
        IPF blog: https://ipfabric.io/blog/end-to-end-path-simulation-with-api/
        """
        parameters = dict(
            startingPoint=src_ip,
            type="pathLookup",
            pathLookupType="hostToDefaultGW",
            groupBy=grouping
        )
        return self.submit_query(parameters)

    async def submit_query(self, parameters):
        res = await self.api.post(
            URIs.end_to_end_path,
            json=dict(
                parameters=parameters,
                snapshot=self.active_snapshot
            )
        )
        res.raise_for_status()
        return res.json()
    
    @staticmethod
    def tcp_flags(parameters, flags):
        if parameters['protocol'] == 'tcp' and flags:
            if(all(x in ['ack', 'fin', 'psh', 'rst', 'syn', 'urg'] for x in flags)):
                parameters['flags'] = flags
            else:
                raise SyntaxError("Only accepted TCP flags are ['ack', 'fin', 'psh', 'rst', 'syn', 'urg']")
        return parameters
    
    @staticmethod
    def check_ips(parameters):
        try:
            src_net = ipaddress.IPv4Network(parameters['startingPoint'], strict=False)
        except ipaddress.AddressValueError:
            raise ipaddress.AddressValueError("Source IP is not a valid IP or subnet.")
        try:
            dst_net = ipaddress.IPv4Network(parameters['destinationPoint'], strict=False)
        except ipaddress.AddressValueError:
            raise ipaddress.AddressValueError("Destination IP is not a valid IP or subnet.")
        if parameters['pathLookupType'] == 'multicast' and (src_net.prefixlen != 32 or dst_net.prefixlen != 32):
            raise SyntaxError("Multicast lookups requires single Source and Group IP's, not subnets.")
        
        parameters['networkMode'] = True if src_net.prefixlen != 32 or dst_net.prefixlen != 32 else False
        return parameters
