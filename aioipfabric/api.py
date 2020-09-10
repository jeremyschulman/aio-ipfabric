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

    def __init__(self, base_url, loop, token=None, username=None, password=None):
        """
        Initialize the asyncio client session to the IP Fabric API

        Parameters
        ----------
        base_url: str
            The base URL of the IP fabric system

        loop:
            The asyncio loop associated with this client.

        token: str
            The refresh token

        username: str
            The login user-name

        password: str
            The login password
        """
        super().__init__(base_url=base_url, verify=False)

        self.__refresh_token = token
        self.__access_token = None

        async def init_login():
            """ obtain the initial access token """
            if all((username, password)):
                await self.__login(username=username, password=password)
            elif token:
                await self.__refresh_access_token(token)
            else:
                raise RuntimeError("MISSING required token or (username, password)")

        self.headers["Content-Type"] = "application/json"

        loop.run_until_complete(init_login())
        self.headers["Authorization"] = f"Bearer {self.__access_token}"

    @property
    def token(self):
        """ return the Refresh Token for later use/storage """
        return self.__refresh_token

    async def refresh_token(self, token: Optional[str] = None):
        """ using the refresh token, obtain a new access token """

        if token:
            self.__refresh_token = token

        assert self.__refresh_token is not None
        await self.__refresh_access_token(self.__refresh_token)
        self.headers["Authorization"] = f"Bearer {self.__access_token}"

    async def __refresh_access_token(self, refresh_token):
        """ underlying API call to update the access token """
        res = await self.post(URIs.token_refresh, json={"refreshToken": refresh_token})
        res.raise_for_status()
        body = res.json()
        self.__access_token = body["accessToken"]

    async def __login(self, username, password):
        """ underlying API to call to authenticate using login credentials """
        res = await self.post(
            URIs.login, json={"username": username, "password": password}
        )
        res.raise_for_status()
        body = res.json()
        self.__access_token = body["accessToken"]
        self.__refresh_token = body["refreshToken"]
