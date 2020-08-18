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
# Private Improts
# -----------------------------------------------------------------------------

from .mixin_inventory import IPFInventoryMixin
from .mixin_configs import IPFConfigsMixin

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = ["IPFabricClient"]


# -----------------------------------------------------------------------------
#
#                           CODE BEGINS
#
# -----------------------------------------------------------------------------


class IPFabricClient(IPFInventoryMixin, IPFConfigsMixin):
    """
    An instance IPFabricClient is used to interact with the IP Fabric
    system API via methods that abstract the underlying API calls.

    The IPFabricClient is composed of mixins, each of which address a different
    aspect of the IP Fabric product.  This composition structure allows the
    Developer to define a client with only those feature aspects that they need
    for their program.
    """

    pass
