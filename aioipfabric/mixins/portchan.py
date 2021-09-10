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

# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

from dataclasses import dataclass
from enum import Enum
import re

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------

from httpx import Response

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from aioipfabric.base_client import IPFBaseClient, table_api
from aioipfabric.consts import TableFields

# -----------------------------------------------------------------------------
#
#                                 CODE BEGINS
#
# -----------------------------------------------------------------------------

DEFAULT_PORTCHAN_MEMBER_COLUMNS = [
    "sn",
    "hostname",
    "intName",
    "siteName",
    "protocol",
    "members",
]


@dataclass
class URIs:
    """identifies API URL endpoints used"""

    member_status = "/tables/interfaces/port-channel/member-status"


class PortChannelMemberStates(str, Enum):
    up = "UP"
    down = "DOWN"
    up_bundled = "P"
    up_not_bunded = "I"
    bundled = "BNDL"
    inactive = "D"
    suspended = "S"


_re_portmember = re.compile(r"(?P<intName>\S+)\((?P<state>\w+)\)")


class IPFPortChannelsMixin(IPFBaseClient):
    """Mixin for Port-Channels"""

    @table_api
    async def fetch_portchannels(self, request: dict) -> Response:
        request.setdefault(TableFields.columns, DEFAULT_PORTCHAN_MEMBER_COLUMNS)
        return await self.api.post(URIs.member_status, json=request)

    @staticmethod
    def xfrec_portchannel_members(rec):
        """
        The purpose of this function is to translate the 'members' string value
        into a list[dict] where each dict has:
            intName: str
            status: PortChannelMemberStatus (enum)

        The update is made _in place_ so that the new rec['members'] is the
        list[dict] and the original string value is no longer available.

        Parameters
        ----------
        rec: dict
            The table record in native format
        """
        members = rec.pop("members").split(", ")
        xf_members = rec["members"] = list()
        for member in members:
            if (mo := _re_portmember.match(member)) is None:
                raise RuntimeError(f"ERROR: port-channel member failed parse: {member}")

            mo_d = mo.groupdict()
            xf_members.append(
                dict(
                    intName=mo_d["intName"],
                    state=PortChannelMemberStates(mo_d["state"]),
                )
            )

    @staticmethod
    def xf_portchannel_members(records):
        for rec in records:
            IPFPortChannelsMixin.xfrec_portchannel_members(rec)
