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
# System Improts
# -----------------------------------------------------------------------------

from typing import Optional, AnyStr
from os import environ, getenv

# -----------------------------------------------------------------------------
# Private Improts
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


class IPFBaseClient(object):
    """
    The IPFabricClient instances is composed of one or more Mixins that are a
    subclass of IPFBaseClient.  Put another way, he IPFBaseClient provides the
    common code that is available to all Mixins.

    The primary purpose of the IPFBaseClass instance is to provide the `api`
    attribute, which is an instance of the IPFSession (async HTTP client
    instance).
    """

    def __init__(
        self,
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

        if not base_url.endswith("/"):
            base_url += "/"

        self.api = IPFSession(
            base_url=base_url + API_VER,
            token=token,
            username=username,
            password=password,
        )
