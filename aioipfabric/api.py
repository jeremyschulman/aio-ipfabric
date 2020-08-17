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

import asyncio
from typing import Optional

from httpx import AsyncClient

from .consts import URIs


class IPFSession(AsyncClient):
    def __init__(self, base_url, token=None, username=None, password=None):

        super().__init__(base_url=base_url, verify=False)

        self.__refresh_token = token
        self.__access_token = None

        async def init_login():
            if all((username, password)):
                await self.__login(username=username, password=password)
            elif token:
                await self.__refresh_access_token(token)
            else:
                raise RuntimeError("MISSING required token or (username, password)")

        loop = asyncio.get_event_loop()
        loop.run_until_complete(init_login())

        self.headers["Content-Type"] = "application/json"
        self.headers["Authorization"] = f"Bearer {self.__access_token}"

    @property
    def token(self):
        """ return the Refresh Token for later use/storage """
        return self.__refresh_token

    async def refresh_token(self, token: Optional[str] = None):
        assert self.__refresh_token is not None
        await self.__refresh_access_token(self.__refresh_token)

    async def __refresh_access_token(self, refresh_token):
        res = await self.post(URIs.token_refresh, json={"refreshToken": refresh_token})
        res.raise_for_status()
        body = res.json()
        self.__access_token = body["accessToken"]

    async def __login(self, username, password):
        res = await self.post(
            URIs.login, json={"username": username, "password": password}
        )
        res.raise_for_status()
        body = res.json()
        self.__access_token = body["accessToken"]
        self.__refresh_token = body["refreshToken"]
