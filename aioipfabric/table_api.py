#  Copyright 2022 Jeremy Schulman
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

from functools import wraps

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from .consts import TableFields

# -----------------------------------------------------------------------------
#
#                                 CODE BEGINS
#
# -----------------------------------------------------------------------------


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
