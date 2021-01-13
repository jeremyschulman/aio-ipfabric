from aioipfabric.filters import parse_filter


def test_simple_filter():
    res = parse_filter("hostname = Foo")
    assert res == {"hostname": ["eq", "Foo"]}


def test_group_filter_and():
    res = parse_filter("and( hostname = Foo, interface = bar)")
    assert res == {"and": [{"hostname": ["eq", "Foo"]}, {"interface": ["eq", "bar"]}]}


def test_group_filter_or():
    res = parse_filter("or( hostname = Foo, interface = bar)")
    assert res == {"or": [{"hostname": ["eq", "Foo"]}, {"interface": ["eq", "bar"]}]}


def test_group_filter_compound_and():
    res = parse_filter("and(hostname = Boo, or( hostname = Foo, interface = bar))")
    inner = {"or": [{"hostname": ["eq", "Foo"]}, {"interface": ["eq", "bar"]}]}
    expected = {"and": [{"hostname": ["eq", "Boo"]}, inner]}
    assert res == expected
