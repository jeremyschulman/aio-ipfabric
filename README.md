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

### Simple test run:

````python
import asyncio
from aioipfabric import IPFabricClient

# Used to ignore nagging httpx client warning (keeping client persistent is by design for the moment)
import warnings
warnings.filterwarnings('ignore', '.*https://www.python-httpx.org/async/#opening-and-closing-clients.*',)

loop = asyncio.get_event_loop()

# create a client using environment variables (see next section)
ipf = IPFabricClient()


# Example for inline vars definition:
# URL_BASE_IPFABRIC = "https://xxx"
# IPFABRIC_USER = "xxx"
# IPFABRIC_PW = "xxx"
# ipf = IPFabricClient(
#     base_url=URL_BASE_IPFABRIC, 
#     username=IPFABRIC_USER, 
#     password=IPFABRIC_PW
# )


# login to IP Fabric system
loop.run_until_complete(ipf.login())

# fetch the complete device inventory
device_list = loop.run_until_complete(ipf.fetch_devices())
print(f"{len(device_list)} devices present under IPF")
````

### Getting a table

From the "?" in the table headers, extract the columns and the resource path (listed under API Document / URL)
This method has been tested on several tables but could have some caveats requiring a specifix mixin.

````python
columns = ["id","sn","hostname","siteKey","siteName","peer","intName","username","group","time","status"]
resourcepath= "/tables/security/ipsec"

loop.run_until_complete(ipf.fetch_table(resourcepath=resourcepath,columns=columns))
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

