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
        "and (site = atl, hostname has sw2, vendor = cisco)"

    Either site is euqal to 'atl' or hostname contains 'sw2'
        "or (site = atl, hostname has sw2)"

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
        "=": "eq",
        "!=": "neq",
        "has": "like",
        "!has": "notlike",
        "=~": "reg",
        "!=~": "nreg",
        "empty": "empty",
        "net": "cidr",
        "<": "le",
        "<=": "lte",
        ">": "gt",
        ">=": "gte",
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
simple_expr         = col_name ws oper ws cmp_value_tok
#
# Token parts
#
col_name        = ~"[a-z0-9]+"i
sq_words        = ~"[^']+"
dq_words        = ~"[^\"]+"
ws              = ~"\s*"
sq              = "'"
dq              = "\""
word            = ~r"[\S]+"
group_tok       = 'and' / 'or'
oper            = '!=~' / '=~' / '!=' / 'net' / '!has' / '<=' / '>=' / '=' / 'has' / 'empty'  / '<' / '>'
cmp_value_tok   = word / sq_tok / dq_tok
sq_tok          = sq sq_words sq
dq_tok          = dq dq_words dq
"""

_grammer = Grammar(FILTER_GRAMMER)


class _FilterConstructor(NodeVisitor):
    def visit_group_expr(self, node, vc):  # noqa
        group_tok, _, _, _, filter_list, *_ = vc
        return {group_tok: filter_list}

    def visit_group_expr_list(self, node, vc):  # noqa
        expr_1, _, expr_n = vc
        expr_list = [
            expr_1,
            *(expr for expr in chain.from_iterable(expr_n) if isinstance(expr, dict)),
        ]
        return expr_list

    def visit_expr_list(self, node, vc):  # noqa
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
        (col, _, oper, _, val,) = vc

        if oper == "empty":
            if (val := {"true": True, "false": False}.get(val.lower())) is None:
                raise RuntimeError("'empty' value must be either 'true' or 'false'")

        return {col: [oper, val]}

    def visit_oper(self, node, vc):  # noqa
        return _OPERATORS[node.text]

    def visit_group_tok(self, node, vc):  # noqa
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
        return int(node.text)

    def visit_col_name(self, node, vc):  # noqa
        return node.text

    def generic_visit(self, node, visited_children):
        return visited_children or node


_filter_builder = _FilterConstructor()


def parse_filter(expr):
    res = _grammer.parse(expr.strip().replace("\n", ""))
    return _filter_builder.visit(res)[0]
