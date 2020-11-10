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

from typing import Optional
from dataclasses import dataclass
import asyncio

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------

from httpx import AsyncClient

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = ["IPFSession"]


# -----------------------------------------------------------------------------
#
#                           CODE BEGINS
#
# -----------------------------------------------------------------------------


@dataclass
class URIs:
    """ identifies API URL endpoings used"""

    login = "auth/login"
    token_refresh = "auth/token"


class IPFSession(AsyncClient):
    """
    The IPFSession instance is the asyncio base client used to interact with the
    IP Fabric API via REST calls.  The primary feature of the IPFSession class
    is to handle the authentication via login credentials and tokens.

    An instance of this class will be created by the IPFBaseClient, which in
    turns makes the api accessbile to any IPFabricClient instances.
    """

    API_THROTTLE = 100

    def __init__(self, base_url, token=None, username=None, password=None):
        """
        Initialize the asyncio client session to the IP Fabric API

        Parameters
        ----------
        base_url: str
            The base URL of the IP fabric system

        token: str
            The refresh token

        username: str
            The login user-name

        password: str
            The login password
        """
        super().__init__(base_url=base_url, verify=False)

        self.__sema4 = asyncio.Semaphore(self.API_THROTTLE)

        self.__refresh_token = token
        self.__access_token = None

        if all((username, password)):
            self.__init_auth = self.__auth_userpass(
                username=username, password=password
            )
        elif token:
            self.__init_auth = self.refresh_token(token)
        else:
            raise RuntimeError("MISSING required token or (username, password)")

        self.headers["Content-Type"] = "application/json"

    # -------------------------------------------------------------------------
    #
    #                             Properties
    #
    # -------------------------------------------------------------------------

    @property
    def token(self):
        """ return the Refresh Token for later use/storage """
        return self.__refresh_token

    # -------------------------------------------------------------------------
    #
    #                             Public Methods
    #
    # -------------------------------------------------------------------------

    async def authenticate(self):
        """
        This coroutine is used to authenticate to the IPF server and obtain an access
        token.  This coroutine can be used for both the initial login process as well
        as the token refresh process.
        """

        # the first time this method is called use the coroutine as selected in
        # the __init__ method based on the provided credentials. Any subsequent
        # call to `authenticate` will use `refresh_token`.  The code below uses
        # the try/except catching the RuntimeError to detected the "first use"
        # vs. subsequent uses.

        try:
            await self.__init_auth

        except RuntimeError:
            await self.refresh_token(self.__refresh_token)

    async def refresh_token(self, token: Optional[str] = None):
        """ using the refresh token, obtain a new access token """

        if token:
            self.__refresh_token = token

        assert self.__refresh_token is not None
        await self.__refresh_access_token(self.__refresh_token)
        self.headers["Authorization"] = f"Bearer {self.__access_token}"

    # -------------------------------------------------------------------------
    #
    #                             Private Methods
    #
    # -------------------------------------------------------------------------

    async def __refresh_access_token(self, refresh_token):
        """ underlying API call to update the access token """
        res = await self.post(URIs.token_refresh, json={"refreshToken": refresh_token})
        res.raise_for_status()
        body = res.json()
        self.__access_token = body["accessToken"]

    async def __auth_userpass(self, username, password):
        """ underlying API to call to authenticate using login credentials """
        res = await self.post(
            URIs.login, json={"username": username, "password": password}
        )
        res.raise_for_status()
        body = res.json()
        self.__access_token = body["accessToken"]
        self.__refresh_token = body["refreshToken"]
        self.headers["Authorization"] = f"Bearer {self.__access_token}"

    # -------------------------------------------------------------------------
    #
    #                             Override Methods
    #
    # -------------------------------------------------------------------------

    async def request(self, *vargs, **kwargs):
        async with self.__sema4:
            return await super(IPFSession, self).request(*vargs, **kwargs)
