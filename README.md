# Python Asyncio Client for IP Fabric

This package contains a Python 3.8+ asyncio client for use wih the IP Fabric product.

   * About IP Fabric: https://ipfabric.io/
   * About IP Fabric API: https://docs.ipfabric.io/api/


[![Downloads](https://pepy.tech/badge/aio-ipfabric)](https://pepy.tech/project/aio-ipfabric)
![Supported Python Version](https://img.shields.io/pypi/pyversions/aio-ipfabric)
![Contributors](https://img.shields.io/github/contributors/jeremyschulman/aio-ipfabric)
[![License](https://img.shields.io/github/license/jeremyschulman/aio-ipfabric)](https://github.com/jeremyschulman/aio-ipfabric/blob/main/LICENSE)


# Installating aio-ipfabric and supported versions

aio-ipfabric is available on [PyPI](https://pypi.org/project/aio-ipfabric/):

```shell script
pip install aio-ipfabric
```

Direct installation
```shell script
pip install git+https://github.com/jeremyschulman/aio-ipfabric@master#egg=aio-ipfabric
```

Requests officially supports Python 3.8+.


# Quick Start

````python
from aioipfabric import IPFabricClient

async def demo_1_devices_list():
    """
    Example code that uses IPFabricClient without contextmanager
    """

    # create a client using environment variables (see next section)
    ipf = IPFabricClient()

    # alternatively create instance with parameters
    # ipf = IPFabricClient(base_url='https://myipfserver.com', username='admin', password='admin12345')
    # ipf = IPFabricClient(base_url='https://myipfserver.com', token='TOKENFROMIPF')
    
    # login to IP Fabric system
    await ipf.login()

    # fetch the complete device inventory
    device_list = await ipf.fetch_devices()
    
    # close asyncio connection, otherwise you will see a warning.
    await ipf.logout()
    
    return device_list

async def demo_2_devices_list():
    """
    Example code that uses IPFabricClient as contextmanager
    """

    # create a client using environment variables (see next section)
    async with IPFabricClient() as ipf:
        return await ipf.fetch_devices()    
````


## Environment Variables

The following environment variable can be used so that you do no need to
provide them in your program:

   * `IPF_ADDR` - IP Fabric server URL, for example "https://my-ipfabric-server.com/"
   * `IPF_USERNAME` - Login username
   * `IPF_PASSWORD` - Login password
   * `IPF_TOKEN` - A persistent API token

You can use either the login credentials or the token to login.

If you prefer not to use environment variables, the call to `IPFabricClient()` accepts
parameters; refer to the `help(IPFabricClient)` for details.

# Documentation

See the [docs](docs) directory.

