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
