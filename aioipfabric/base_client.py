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
import http

# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

from typing import Optional, AnyStr, Iterable, List, Dict, Union
from os import environ, getenv
from dataclasses import dataclass

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------

from httpx import Response

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from .api import IPFSession
from .filters import parse_filter
from .table_api import table_api

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
    """identifies API URL endpoings used"""

    snapshots = "/snapshots"


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
        """identifies enviornment variables used"""

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
        **clientopts,
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
            The IP Fabric API Token created from the Settings configuration;
            requires IP Fabric v3.7+

        Other Parameters
        ----------------
        `clientopts` are passed AS-IS to the API session so that the
        httpx.AsyncClient can be configured as desired.

        Notes
        -----
        The Caller can provide either the login credentials (username, password)
        or the refresh token.  One of these two are required.
        """

        token = token or getenv(self.ENV.token)
        base_url = base_url or environ[self.ENV.addr]
        username = username or getenv(self.ENV.username)
        password = password or getenv(self.ENV.password)

        # if the Caller does not provide a base_url that has the '/api/v'
        # substring then use the default API version for the class.

        self.api = IPFSession(
            base_url=base_url,
            token=token,
            username=username,
            password=password,
            **clientopts,
        )

        # dynamically add any Mixins at the time of client creation.  This
        # enables the caller to perform the mixin at runtime without having to
        # define a specific class.

        if mixin_classes:
            self.mixin(*mixin_classes)

        self.snapshots = None
        self._active_snapshot = None
        self.version = None  # the IPF product version

    @property
    def active_snapshot(self):
        return self._active_snapshot

    @active_snapshot.setter
    def active_snapshot(self, name):
        if (
            s_id := next((i["id"] for i in self.snapshots if i["name"] == name), None)
        ) is None:
            raise ValueError(name)
        self._active_snapshot = s_id

    async def discover_api_version(self):
        """
        If the '/api/v' substring is to provided by the Caller then this
        method will attempt to discover the IPF product version.  As of v5,
        there is a new endpoint '/api/version' that does NOT require
        authentication to acceess. if that endpoint exists, then use the
        version in the response payload to form the basse URL.  If then
        endpoint does not exist (404) then using a version of IPF < v5.
        """

        res = await self.api.get("/api/version")

        self.api.base_url = self.api.base_url.join(
            "/api/v1/"
            if res.status_code == http.HTTPStatus.NOT_FOUND
            else f"/api/{res.json()['apiVersion']}"
        )

    async def login(self):
        """
        Coroutine to perform the initial login authentication process, retrieve the list
        of current snapshots, and set the `active_snapshot` attribute to the latest loaded
        snapshot.
        """

        if "/api/v" not in str(self.api.base_url):
            await self.discover_api_version()

        if self.api.token and self.api.is_closed:
            self.api = IPFSession(base_url=str(self.api.base_url), token=self.api.token)

        await self.api.authenticate()

        # if the `version` attribute is set this means that this client has
        # connected to the IPF system before, and we do not need to re-fetch the
        # version and snapshot data.

        if self.version:
            return

        # capture the IPF version value
        res = await self.api.get("/os/version")
        res.raise_for_status()
        self.version = res.json()["version"]

        # fetch the snapshot catalog and default the active to the most recent one.
        # TODO: might want to only fetch the "latest" snapshot vs. all.
        await self.fetch_snapshots()
        self._active_snapshot = next(
            (
                snapshot["id"]
                for snapshot in self.snapshots
                if snapshot["state"] == "loaded"
            ),
            None,
        )

    async def logout(self):
        """close the async connection"""
        await self.api.aclose()

    async def fetch_snapshots(self) -> None:
        """coroutine to retrieve all known snapshots, returns List[dict] records"""
        res = await self.api.get(URIs.snapshots)
        res.raise_for_status()
        self.snapshots = res.json()

    @table_api
    async def fetch_table(self, url: str, request: dict) -> Union[Response, List, Dict]:
        """
        This coroutine is used to fetch records from any table, as identified by
        the `url` parameter.  The `requests` dict *must* contain a columns key,
        and if missing this coroutine will raise a ValueError exception.

        Parameters
        ----------
        url: str
            The URL to indicate the table, for example "/tables/inventory/devices".

        request: dict
            The request body payload, as prepared by the `table_api` decorator.

        """
        return await self.api.post(url=url, json=request)

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
        """override the default repr to show the IPF system base URL"""
        cls_name = self.__class__.__name__
        base_url = self.api.base_url
        return f"{cls_name}: {base_url}"

    # -------------------------------------------------------------------------
    #
    #                      ASYNC CONTEXT MANAGER METHODS
    #
    # -------------------------------------------------------------------------

    async def __aenter__(self):
        """login and return instance"""
        await self.login()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """close the http async api instance"""
        await self.logout()

    # -------------------------------------------------------------------------
    #
    #                             STATIC METHODS
    #
    # -------------------------------------------------------------------------

    parse_filter = staticmethod(parse_filter)
