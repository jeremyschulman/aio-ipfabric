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

"""
This file contains API helpers for filtering data.  At the time of v3.6, the
online documentation can be found here:
https://docs.ipfabric.io/api/#header-filter-structure.  Unfortunately the
content is lacking many details.

Examples
--------
Simple Expressions:

    "hostname = foo"
    "hostname =~ 'abc.*'"

Grouped Expressions:
    Both site is equal to 'atl' and hostname contains 'sw2'
    and (site = atl, hostname has sw2, vendor = cisco)

    Either site is euqal to 'atl' or hostname contains 'sw2'
    or (site = atl, hostname has sw2)

Nested Group Expressions:
    or (
        and(site = atl, hostname has 'core'),
        and(site = chc, hostname =~ '.*club-switch2[12]')
    )


References
----------
    IP Fabric API docs:
    https://docs.ipfabric.io/api/#header-filter-structure.

    Parsimonious:
    https://github.com/erikrose/parsimonious

Notes
-----
Filter options for <string> type

    ["eq", <string | null>] - equal to a string
    ["neq", <string | null>] - not equal to a string
    ["like", <string | null>] - contain a string
    ["notlike", <string | null>] - not contain a string
    ["reg", <string | null>] - match a regular expression
    ["nreg", <string | null>] - not match a regular expression
    ["empty", <boolean>] - (not) empty

Filter options for <IP address> type

    ["cidr", <IPv4 in CIDR notation>] - fit in a range
    ["eq", <string | null>] - equal to a string
    ["neq", <string | null>] - not equal to a string
    ["like", <string | null>] - contain a string
    ["notlike", <string | null>] - not contain a string
    ["reg", <string | null>] - match a regular expression
    ["nreg", <string | null>] - not match a regular expression
    ["empty", <boolean>] - (not) empty

Filter options for <number> type

    ["eq", <number | null>] - equal to a number
    ["neq", <number | null>] - not equal to a number
    ["gt", <number | null>] - greater than a number
    ["gte", <number | null>] - greater than or equal to a number
    ["lt", <number | null>] - lower than a number
    ["lte", <number | null>] - lower than or equal to a number
    ["empty", <boolean>] - (not) empty

* Filter by "column" comparison
    For example, on the Inventory|Interfaces table, using this filter will compare the value
    of the "l1" column to the "l2" column:

    { "filters": {"l1":["column","eq","l2"]}
"""
# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

from types import MappingProxyType
from itertools import chain

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------

from parsimonious import Grammar, NodeVisitor
from parsimonious.nodes import RegexNode

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = ["parse_filter"]

# -----------------------------------------------------------------------------
#
#                                 CODE BEGINS
#
# -----------------------------------------------------------------------------

_OPERATORS = MappingProxyType(
    {
        "=": "eq",  # equals exactly
        "!=": "neq",  # does not equal
        "has": "like",  # string contains
        "!has": "notlike",  # string does not contain
        "=~": "reg",  # match regular expression
        "!=~": "nreg",  # does not match regular expression
        "empty": "empty",  # column is empty
        "net": "cidr",  # value match using IP CIDR value
        "<": "lt",  # less than
        "<=": "lte",  # less than or equal to
        ">": "gt",  # greater than
        ">=": "gte",  # greather than or equal to
    }
)


FILTER_GRAMMER = r"""
#
# Expression parts
#
filter_expr         = group_expr / simple_expr
group_expr_list     = group_expr ws ("," ws group_expr)+
group_expr          = group_tok ws "(" ws expr_list ws ")"
expr_list           = simple_expr_list / group_expr_list
simple_expr_list    = simple_expr ws ("," ws simple_expr)+
simple_expr         = col_name ws (column_expr_rhs / color_expr_rhs / oper_expr_rhs)
oper_expr_rhs       = oper ws cmp_value_tok
column_expr_rhs     = "column" ws oper ws col_name
color_expr_rhs      = "color" ws oper ws cmp_value_tok
#
# Token parts
#
col_name        = ~"[a-z0-9]+"i
sq_words        = ~"[^']+"
dq_words        = ~"[^\"]+"
ws              = ~"\s*"
sq              = "'"
dq              = "\""
word            = ~r"[a-z0-9\.\/]+"
group_tok       = 'and' / 'or'
oper            = '!=~' / '=~' / '!=' / 'net' / '!has' / '<=' / '>=' / '=' / 'has' / 'empty'  / '<' / '>'
cmp_value_tok   = sq_tok / dq_tok / word
sq_tok          = sq sq_words sq
dq_tok          = dq dq_words dq
"""

_grammer = Grammar(FILTER_GRAMMER)


class _FilterConstructor(NodeVisitor):
    """ parsimouneous node visitor for handlingn the FILTER_GRAMMER """

    def visit_group_expr(self, node, vc):  # noqa
        """ create a group_expr item """
        group_tok, _, _, _, filter_list, *_ = vc
        return {group_tok: filter_list}

    def visit_group_expr_list(self, node, vc):  # noqa
        """ create a list of group_expr items """
        expr_1, _, expr_n = vc
        expr_list = [
            expr_1,
            *(expr for expr in chain.from_iterable(expr_n) if isinstance(expr, dict)),
        ]
        return expr_list

    def visit_expr_list(self, node, vc):  # noqa
        """ create an expr_list item """
        return vc[0]

    def visit_simple_expr_list(self, node, vc):  # noqa
        """ return a list of filter dictionaries """
        expr_1, _, expr_n = vc
        return [
            expr_1,
            *(expr for expr in chain.from_iterable(expr_n) if isinstance(expr, dict)),
        ]

    def visit_simple_expr(self, node, vc):  # noqa
        """ return a filter dictionary """
        col, rhs = vc[0], vc[2][0]

        if rhs[0] == "empty":
            val = rhs[1]
            if (val := {"true": True, "false": False}.get(val.lower())) is None:
                raise RuntimeError("'empty' value must be either 'true' or 'false'")
            rhs[1] = val

        return {col: rhs}

    def visit_oper_expr_rhs(self, node, vc):  # noqa
        """ returns the operattor right-hand-side expression list item """
        oper, _, value_tok = vc
        return [oper, value_tok]

    def visit_column_expr_rhs(self, node, vc):  # noqa
        """ return the 'column' operation right-hand-side expression list item"""
        col_oper, _, oper, _, col_name = vc
        return [col_oper.text, oper, col_name]

    def visit_color_expr_rhs(self, node, vc):  # noqa
        """ return the 'column' operation right-hand-side expression list item"""
        col_oper, _, oper, _, col_val = vc
        return [col_oper.text, oper, col_val]

    def visit_oper(self, node, vc):  # noqa
        """ converts the grammer operator to an IPF filter operator """
        return _OPERATORS[node.text]

    def visit_group_tok(self, node, vc):  # noqa
        """ returns the group operator (and, or) value """
        return node.text

    def visit_cmp_value_tok(self, node, vc):  # noqa
        """ children will either be a single node-value or a quoted-value """
        vc = vc.pop(0)

        if isinstance(vc, RegexNode):
            # return as number if int-able
            try:
                return int(vc.text)
            except ValueError:
                return vc.text

        value_node = vc[0] if len(vc) == 1 else vc[1]
        return value_node.text

    def visit_number(self, node, vc):  # noqa
        """ returns the value as an integer """
        return int(node.text)

    def visit_col_name(self, node, vc):  # noqa
        """ returns the column name (str) """
        return node.text

    def generic_visit(self, node, visited_children):
        """ pass through for nodes not explicility visited """
        return visited_children or node


_filter_builder = _FilterConstructor()


def parse_filter(expr: str) -> dict:
    """
    This function is used to convert a filter expression, as a string in the form
    of FILTER_GRAMMER, and return the IPF filter dictionary that is consumed by
    the `filters` body parameters.

    Parameters
    ----------
    expr
        The filter expression, for example "hostname = switch1.dc1"
    """
    res = _grammer.parse(expr.strip().replace("\n", ""))
    return _filter_builder.visit(res)[0]
