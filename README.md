# Python Asyncio Client for IP Fabric

This package contains a Python 3.8 asyncio client for use wih the IP Fabric product.

   * About IP Fabric: https://ipfabric.io/
   * About IP Fabric API: https://docs.ipfabric.io/api/


# Installation

PyPi installation
```shell script
pip install aio-ipfabric
```

Direct installation
```shell script
pip install git+https://github.com/jeremyschulman/aio-ipfabric@master#egg=aio-ipfabric
```

# Quick Start

````python
import asyncio
from aioipfabric import IPFabricClient

loop = asyncio.get_event_loop()

# create a client using environment variables (see next section)
ipf = IPFabricClient()

# login to IP Fabric system
loop.run_until_complete(ipf.login())

# fetch the complete device inventory
device_list = loop.run_until_complete(ipf.fetch_devices())
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

# Documentation

See the [docs](docs) directory.

