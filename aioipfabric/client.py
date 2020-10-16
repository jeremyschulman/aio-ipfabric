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

from typing import List, Dict, Optional, AnyStr
import csv

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from aioipfabric.mixins.inventory import IPFInventoryMixin

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = ["IPFabricClient"]


# -----------------------------------------------------------------------------
#
#                                 CODE BEGINS
#
# -----------------------------------------------------------------------------


class IPFabricClient(IPFInventoryMixin):
    """
    An instance IPFabricClient is used to interact with the IP Fabric
    system API via methods that abstract the underlying API calls.

    The IPFabricClient is composed of mixins, each of which address a different
    aspect of the IP Fabric product.  This composition structure allows the
    Developer to define a client with only those feature aspects that they need
    for their program.

    To dynamically add a Mixin class, use the `mixin` method defined
    by `IPFBaseClass`

    Examples
    --------
        from aioipfabric import IPFabricClient
        from aioipfabric.mixin_configs import IPFConfigMixin

        ipf = IPFabricClient()
        ipf.mixin(IPFConfigMixin)

    """

    @staticmethod
    def to_csv(
        datalist: List[Dict],
        filepath: AnyStr,
        fieldnames: Optional[List[str]] = None,
        exclude: Optional[List[str]] = None,
    ) -> None:
        """
        This method will store the given list of dict items to a CSV file.  The
        CSV column headers will be taken from the first list item keys.  The
        `exclude` list can be used to omit designated columns from the CSV file,
        for exampel ['id'] would omit the 'id' column.

        Parameters
        ----------
        datalist
        filepath
        exclude
        fieldnames
        """
        dl_fieldnames = datalist[0].keys()

        if fieldnames:
            _s_fieldnames = set(fieldnames)
            _s_dl_fieldnames = set(dl_fieldnames)

            if _s_fieldnames & _s_dl_fieldnames != _s_fieldnames:
                raise RuntimeError(f"Invalid set of fieldnames: {fieldnames}")

            exclude = _s_dl_fieldnames - _s_fieldnames
        else:
            fieldnames = dl_fieldnames

        if exclude:
            fieldnames = [col for col in fieldnames if col not in exclude]
            for rec in datalist:
                for key in exclude:
                    del rec[key]

        with open(filepath, "w+") as ofile:
            csv_wr = csv.DictWriter(ofile, fieldnames=fieldnames)
            csv_wr.writeheader()
            csv_wr.writerows(datalist)
