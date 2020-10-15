# IPF Client Extensions

This page describes the process to add new features to the IP Client instance
using the Pythonic Mixins approach.

The IP Fabric product offers a very rich set of features that are not
immediately provided by the `aioipfabric` client library.  As a method to enable
a Developer to add what they want, the `IPFabricClient` class can be dynamically
extended using the concept of a Mixin.

What this means is that as a Developer you can define a new class that is
subclassed from `IPFBaseClass` that includes new methods for the API features
you want to provide.

See [IPFConfigMixin](../aioipfabric/mixin_configs.py) for example.

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
