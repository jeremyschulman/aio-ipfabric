# IP Fabric Table Filtering

IP Fabric Table APIs allow you to provide a `filters` in the body payload.  The
structure of the `filters` value is a dictionary whose value is described from
within the product pages, but not readily accessible.  As a result the
`aio-ipfabric` client provides a helper method called `parse_filter()` that
takes a string expression and translates it into the API dictionary structure.

For complete documentation of the available filtering expressions (aka parsing
grammar), please refer to the code [filters.py](../aioipfabric/filters.py).

# Filter Operators
  * `A = B `  - A exactly equals B; supporing string and numeric
  * `A =~ B` - A matches regular expression B.  Need to quote the reqular expression (see Example)
  * `A ~ B ` - A contains the substring
  * `A ? true` - A contains any value


  * `A != B` - A does not exactly match B; supporting string and numeric
  * `A !=~ B` - A does not match the regular expression B
  * `A !~ B` - A does not contain the substring B <br/>
  * `A ? false` - A is empty

**Numeric Only**
  * `A < B` - A is less than B
  * `A <= B` - A is less than or equal to B
  * `A > B` - A is greater than B
  * `A >= B` - A is greater than or equal to B <br/>

**Special**
  * `A column <operator> B` - Used to compare one column with another (see Example)
  * `A color <operator> B` - Used to retrieve invent verifcation rule report results (see Example)
  * `A net B` - Find IP addresses in column A that are in the subnet B.

# Examples

**Simple Expressions**<br/>

Find a record with the `hostname` column equal exactly the value "foo"
```python
filter_expr = "hostname = foo"
```

Find all records with the `hostname` column matching the reqular expression "abc.*"
```python
filter_expr = "hostname =~ 'abc.*'"
```

Find all records with the `hostname` column containing the string "abc"
```
filter_expr = "hostname ~ abc"
```

**Grouped Expressions**<br/>

Both site is equal to 'atl' and hostname contains 'sw2'
```python
filter_expr = "and (site = atl, hostname has sw2, vendor = cisco)"
```

Either site is euqal to 'atl' or hostname contains 'sw2'
```python
filter_expr = "or (site = atl, hostname has sw2)"

```

**Nested Group Expressions**<br/>

```python
filter_expr = """
or (
   and (siteName = atl, hostname has 'core'),
   and (siteName = chc, hostname =~ '.*club-switch2[12]')
)
"""
```

**Columns Matches another Column**<br/>

Find records where the column "l1" has the same value as the column "l2":

```python
filter_expr = "l2 column = l2"
```

Find records where the column "l1" does not have the same value as the column "l2":

```python
filter_expr = "l2 column != l2"
```

**Intent Verification Rules**<br/>
Filtering for the intent verification rule matches uses the "color" operator.  The following
default colors are defined in the IPF API [documents](https://docs.ipfabric.io/api/#header-reports):

   * green = 0
   * blue = 10
   * yellow = 20
   * red = 30

Find all records whose rule assigned to the "intName" column matches yellow (20):
```python
filter_expr = "intName color = 20"
```

Find al records whose role assigned to the "intName" column is greater than "green":
```python
filter_expr = "intName color > 0"
```

**Network CIDR**<br/>
Filter records when columns are IP address to match a give subnet.

Find all records whose login IP address is in the subnet 172.16.20.0/24:
```
filter_expr = "loginIp net 172.16.20.0/24"
```