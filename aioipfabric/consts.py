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

from dataclasses import dataclass


@dataclass
class ENV:
    addr = "IPF_ADDR"
    username = "IPF_USERNAME"
    password = "IPF_PASSWORD"
    token = "IPF_TOKEN"


API_VER = "api/v1/"


@dataclass
class URIs:
    login = "auth/login"
    token_refresh = "auth/token"
    devices = "tables/inventory/devices/"
    managed_ipaddrs = "tables/addressing/managed-devs/"
    device_config_refs = "tables/management/configuration"
    download_device_config = "tables/management/configuration/download"
