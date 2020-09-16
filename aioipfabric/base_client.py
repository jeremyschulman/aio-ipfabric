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

from typing import Optional, AnyStr, Iterable
from os import environ, getenv
from dataclasses import dataclass

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from .consts import ENV, API_VER
from .api import IPFSession

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = ["IPFBaseClient"]


# -----------------------------------------------------------------------------
#
#                           CODE BEGINS
#
# -----------------------------------------------------------------------------


@dataclass
class URIs:
    """ identifies API URL endpoings used"""

    snapshots = "snapshots"


class IPFBaseClient(object):
    """
    The IPFabricClient instances is composed of one or more Mixins that are a
    subclass of IPFBaseClient.  Put another way, he IPFBaseClient provides the
    common code that is available to all Mixins.

    The primary purpose of the IPFBaseClass instance is to provide the `api`
    attribute, which is an instance of the IPFSession (async HTTP client
    instance).
    """

    @dataclass
    class ENV:
        """ identifies enviornment variables used """

        addr = "IPF_ADDR"
        username = "IPF_USERNAME"
        password = "IPF_PASSWORD"
        token = "IPF_TOKEN"

    def __init__(
        self,
        /,
        *mixin_classes,
        base_url: Optional[AnyStr] = None,
        token: Optional[AnyStr] = None,
        username: Optional[AnyStr] = None,
        password: Optional[AnyStr] = None,
    ):
        """
        Create an IP Fabric Client instance

        Parameters
        ----------
        base_url : str
            The IP Fabric system HTTPS URL, for example:
            https://my-ipfabric-server/

        username: str
            The IPF login user-name value

        password: str
            The IPF login password value

        token : str
            The IP Fabric Refresh Token that will be used to create the Access
            Token required by API calls.

        Notes
        -----
        The Caller can provide either the login credentials (username, password)
        or the refresh token.  One of these two are required.
        """

        token = token or getenv(ENV.token)
        base_url = base_url or environ[ENV.addr]
        username = username or getenv(ENV.username)
        password = password or getenv(ENV.password)

        # maintain the asyncio loop for methods that need to act synchronously.
        # self.loop = asyncio.get_event_loop()

        # ensure that the base_url ends with a slash since we will be using
        # httpx with base_url. there is a known _requirement_ for
        # ends-with-slash which if not in place causes issues.

        if not base_url.endswith("/"):
            base_url += "/"

        self.api = IPFSession(
            base_url=base_url + API_VER,
            token=token,
            username=username,
            password=password,
        )

        # dynamically add any Mixins at the time of client creation.  This
        # enables the caller to perform the mixin at runtime without having to
        # define a specific class.

        if mixin_classes:
            self.mixin(*mixin_classes)

        self.snapshots = None
        self.active_snapshot = None

    async def login(self):
        await self.api.authenticate()
        await self.fetch_snapshots()

        self.active_snapshot = self.snapshots[0]["id"]

    async def fetch_snapshots(self) -> None:
        """ coroutine to retrieve all known snapshots, returns List[dict] records """
        res = await self.api.get(URIs.snapshots)
        res.raise_for_status()
        self.snapshots = res.json()

    def mixin(self, *mixin_cls):
        """
        This method allows the Caller to dynamically add a Mixin class
        to the existing IPF client instance.

        Parameters
        ----------
        mixin_cls: subclasses of IPFBaseClass
            The mixin classes whose methods will be added to the existing
            IPF client instance (self).

        References
        ----------
        https://stackoverflow.com/questions/8544983/dynamically-mixin-a-base-class-to-an-instance-in-python
        """
        self.__class__ = type(self.__class__.__name__, (self.__class__, *mixin_cls), {})

    def __repr__(self) -> Iterable[str]:
        """ override the default repr to show the IPF system base URL """
        cls_name = self.__class__.__name__
        base_url = self.api.base_url
        return f"{cls_name}: {base_url}"
