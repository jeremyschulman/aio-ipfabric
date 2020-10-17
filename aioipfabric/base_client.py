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
from functools import wraps

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from .consts import ENV, API_VER, TableFields
from .api import IPFSession
from .filters import parse_filter

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = ["IPFBaseClient", "table_api"]


# -----------------------------------------------------------------------------
#
#                           CODE BEGINS
#
# -----------------------------------------------------------------------------


@dataclass
class URIs:
    """ identifies API URL endpoings used"""

    snapshots = "/snapshots"


def table_api(methcoro):
    """ Method decorator for all Table related APIs """

    @wraps(methcoro)
    async def wrapper(self, request=None, return_as="data", **kwargs):
        """ wrapper that prepares the API with default behaviors """

        payload = request or {}
        payload.setdefault(TableFields.snapshot, self.active_snapshot)
        payload.setdefault(TableFields.filters, kwargs.get(TableFields.filters) or {})

        if TableFields.columns in kwargs:
            payload[TableFields.columns] = kwargs[TableFields.columns]

        # TODO: perhaps add a default_pagination setting to the IP Client?
        #       for now the default will be no pagnication

        if TableFields.pagination in kwargs:
            payload["pagination"] = kwargs[TableFields.pagination]

        res = await methcoro(self, payload)

        if return_as == "raw":
            return res

        res.raise_for_status()
        body = res.json()

        return {"data": body["data"], "meta": body["_meta"], "body": body}[return_as]

    return wrapper


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

        # ensure that the base_url ends with a slash since we will be using
        # httpx with base_url. there is a known _requirement_ for
        # ends-with-slash which if not in place causes issues.
        # TODO: perhaps this issue has been fixed in latter versions of httpx; not
        #       seeing the same issue with httpx > 0.14
        # if not base_url.endswith("/"):
        #     base_url += "/"

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
        self.version = None  # the IPF product version

    async def login(self):
        """
        Coroutine to perform the initial login authentication process, retrieve the list
        of current snapshots, and set the `active_snapshot` attribute to the latest
        snapshot.
        """
        await self.api.authenticate()
        res = await self.api.get("/os/version")
        res.raise_for_status()
        self.version = res.json()["version"]
        await self.fetch_snapshots()

        self.active_snapshot = self.snapshots[0]["id"]

    async def logout(self):
        """ close the async connection """
        await self.api.aclose()

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

    # -------------------------------------------------------------------------
    #                      ASYNC CONTEXT MANAGER METHODS
    # -------------------------------------------------------------------------

    async def __aenter__(self):
        """ login and return instance """
        await self.login()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """ close the http async api instance """
        await self.logout()

    # -------------------------------------------------------------------------
    #                             STATIC METHODS
    # -------------------------------------------------------------------------

    parse_filter = staticmethod(parse_filter)
