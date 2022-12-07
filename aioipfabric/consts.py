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

from enum import Enum

# -----------------------------------------------------------------------------
#
#                                    CODE BEGINS
#
# -----------------------------------------------------------------------------


COLOR_GREEN = 0
COLOR_BLUE = 10
COLOR_YELLOW = 20
COLOR_RED = 30


class TableFields(str, Enum):
    """identifies the API Table request body fields"""

    columns = "columns"
    filters = "filters"
    pagination = "pagination"
    snapshot = "snapshot"
    reports = "reports"
    sort = "sort"


class TableSort(str, Enum):
    ascending = "asc"
    descending = "desc"
