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
        "or (and(site = atl, hostname has sw2), and(site = chc, hostname =~ '.*rs2[12]'"


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
        "?": "empty",
        "/": "cidr",
        "<": "le",
        "<=": "lte",
        ">": "gt",
        ">=": "gte",
    }
)


FILTER_GRAMMER = r"""
filter_expr         = group_expr / simple_expr
group_expr          = group_tok ws "(" ws simple_expr_list ws ")"
simple_expr_list    = simple_expr ws ("," ws simple_expr)+
simple_expr     = col_name ws oper ws cmp_value_tok
col_name        = ~"[a-z0-9]+"i
sq_words        = ~"[^']+"
dq_words        = ~"[^\"]+"
lpar            = "("
rpar            = ")"
ws              = ~"\s*"
sq              = "'"
dq              = "\""
number          = ~"\d+"
word            = ~"[-\w]+"
group_tok       = 'and' / 'or'
oper            = '!=~' / '=~' / '!=' / '!has' / '<=' / '>=' / '=' / 'has' / '?' / '/' / '<' / '>'
cmp_value_tok   = number / word / sq_tok / dq_tok
sq_tok          = sq sq_words sq
dq_tok          = dq dq_words dq
"""

grammer = Grammar(FILTER_GRAMMER)


class _GrammerParser(NodeVisitor):
    def visit_group_expr(self, node, vc):
        group_tok, _, _, _, filter_list, *_ = vc
        return {group_tok: filter_list}

    def visit_simple_expr_list(self, node, vc):
        """ return a list of filter dictionaries """
        expr_1, _, expr_n = vc
        return [
            expr_1,
            *(expr for expr in chain.from_iterable(expr_n) if isinstance(expr, dict)),
        ]

    def visit_simple_expr(self, node, vc):
        """ return a filter dictionary """
        (col, _, oper, _, val,) = vc
        return {col: [oper, val]}

    def visit_oper(self, node, vc):
        return _OPERATORS[node.text]

    def visit_group_tok(self, node, vc):
        return node.text

    def visit_cmp_value_tok(self, node, vc):
        """ children will either be a single node-value or a quoted-value """
        vc = vc.pop(0)

        if isinstance(vc, (int, str)):
            return vc

        if isinstance(vc, RegexNode):
            return vc.text

        value_node = vc[0] if len(vc) == 1 else vc[1]
        return value_node.text

    def visit_number(self, node, vc):
        return int(node.text)

    def visit_col_name(self, node, vc):
        return node.text

    def generic_visit(self, node, visited_children):
        return visited_children or node


nv = _GrammerParser()


def parse_filter(expr):
    res = grammer.parse(expr)
    return nv.visit(res)
