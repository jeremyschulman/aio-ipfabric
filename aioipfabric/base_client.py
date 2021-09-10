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

from typing import Optional, AnyStr, Iterable, List, Dict, Union
from os import environ, getenv
from dataclasses import dataclass
from functools import wraps

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------

from httpx import Response

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
    """identifies API URL endpoings used"""

    snapshots = "/snapshots"


def table_api(methcoro):
    """Method decorator for all Table related APIs"""

    @wraps(methcoro)
    async def wrapper(
        self,
        *,
        filters=None,
        columns=None,
        pagination=None,
        sort=None,
        reports=None,
        request=None,
        return_as="data",
        **kwargs,
    ):
        """
        This decorator prepares a request body used to fetch records from a
        Table.  The wrapped coroutine will be passed at a minimum two
        Parameters, the first being the instance to the IPF client, and a named
        parameter `request` that is a dictionary of the prepared fields.  Any
        other Caller args `kwargs` are passed to the wrapped coroutine as-is.

        The return value is deteremined by the `return_as` parameter.  By
        default, the return value is a list of table records; that is the
        response body 'data' list.  If `return_as` is set to "meta" then the
        return value is the response body 'meta' dict item, which contains the
        keys such as "count" and "size". If the `return_as` is set to "body"
        then return value is the entire native response body that contains both
        the 'data' and '_meta' keys (not the underscore for _meta in this
        case!).  If `return_as` is set to 'raw' then the response is the raw
        httpx.Response object.

        Parameters
        ----------
        self:
            The instance of the IPF Client

        filters: dict
           The IPF filters dictionary item.  If not provided, the
           request['filters'] will be set to an empty dictionary.

        columns: list
            The list of table column names; specific to the Table being fetched.
            If this parameter is None, then the request['columns'] key is not
            set.

        pagination: dict
            The IPF API pagination item.  If not provided, the
            request['pagination'] key is not set.

        sort: dict
            The IPF API sort item.  If not provided, the request['sort'] key is
            not set.

        reports: str
            A request reports string, generally used when retrieving
            intent-rule-validation values.

        request: dict
            If provided, this dict is the starting defition of the request
            passed to the wrapped coroutine.  If not provided, this decorator
            creates a new dict object that is populated based on the above
            description.

        return_as

        Other Parameters
        ----------------
        Any other key-value arguments are passed 'as-is' to the wrapped coroutine.

        Returns
        -------
        Depends on the parameter `return_as` as described above.
        """

        payload = request or {}
        payload.setdefault(TableFields.snapshot, self.active_snapshot)
        payload.setdefault(TableFields.filters, filters or {})

        if columns:
            payload[TableFields.columns] = columns

        # TODO: perhaps add a default_pagination setting to the IP Client?
        #       for now the default will be no pagnication

        if pagination:
            payload["pagination"] = pagination

        if reports:
            payload["reports"] = reports

        if sort:
            payload["sort"] = sort

        res = await methcoro(self, request=payload, **kwargs)

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

        token = token or getenv(ENV.token)
        base_url = base_url or environ[ENV.addr]
        username = username or getenv(ENV.username)
        password = password or getenv(ENV.password)

        self.api = IPFSession(
            base_url=base_url + API_VER,
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

    async def login(self):
        """
        Coroutine to perform the initial login authentication process, retrieve the list
        of current snapshots, and set the `active_snapshot` attribute to the latest
        snapshot.
        """
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
        self._active_snapshot = self.snapshots[0]["id"]

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
