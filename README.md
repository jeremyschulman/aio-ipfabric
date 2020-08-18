# Python Asyncio Client for IP Fabric

This package contains a Python 3.8 asyncio client for use wih the IP Fabric product.

   * About IP Fabric: https://ipfabric.io/
   * About IP Fabric API: https://docs.ipfabric.io/api/


# Installation

This package is not in PyPi so you will need to install it from a local git clone or pip
directly to the repo:

```
pip install git+https://github.com/jeremyschulman/aio-ipfabric@master#egg=aio-ipfabric
```

# Quick Start

````python

import asyncio
from aioipfabric import IPFabricClient

loop = asyncio.get_event_loop()

# login using environment variables (see next section)
ipf = IPFabricClient()

# fetch the complete device inventory
res = loop.run_until_complete(ipf.fetch_devices())
print(res['_meta']['count'])
````

Ouputs:
````python
2316
````

## Environment Variables

The following environment variable can be used so that you do no need to provide them in
your program:

   * `IPF_ADDR` - IP Fabric server URL, for example "https://my-ipfabric-server.com/"
   * `IPF_USERNAME` - Login username
   * `IPF_PASSWORD` - Login password
   * `IPF_TOKEN` - A refresh token that can be used to obtain an access token

You can use either the login credentials or the refresh token to login.

If you prefer not to use environment variables, the call to `IPFabricClient()` accepts
parameters; refer to the `help(IPFabricClient)` for details.

# Mixin based Approach

The IP Fabric product offers a very rich set of features that are not
immediately provided by the `aioipfabric` client library.  As a method to enable
a Developer to add what they want, the `IPFabricClient` class can be dynamically
extended using the concept of a Mixin.  What this means is that as a Developer
you can define a new class that is subclassed from `IPFBaseClass` that includes
new methods for the API features you want to provide.  See
[IPFConfigMixin](aioipfabric/mixin_configs.py) for example.

You can then mixin this class in one of the following ways:

   * At class definition time
   * At instance creation time
   * After instance creation

## At class definition time

You can define your own class that is the composition of Mixins.  This is the "tranditional"
approach to using Mixins.  For example:

````python
from aioipfabric import IPFabricClient
from aioipfabric.mixin_configs import IPFConfigsMixin

class MyClient(IPFConfigsMixin, IPFabricClient):
    pass

# create an instance of the client

ipf = MyClient()
````

## At instance creation time

Another approach is to use the provided `IPFabricClient` class and add the mixins when
the client instance is created.  You can provide one or more mixin classes using this
method.

````python
from aioipfabric import IPFabricClient
from aioipfabric.mixin_configs import IPFConfigsMixin

# create an instance of the client

ipf = IPFabricClient(IPFConfigsMixin)
````

## After instance creation

Another approach is to add the mixin class at runtime after the client has been created (lazy-mixin),
using the `mixin()` method of the IPFabricClient.

````python
from aioipfabric import IPFabricClient
from aioipfabric.mixin_configs import IPFConfigsMixin

# create an instance of the client

ipf = IPFabricClient()

# ... sometime later in the code you decide to add the configs mixin ...

ipf.mixin(IPFConfigsMixin)

````
