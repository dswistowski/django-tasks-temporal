from temporalio.client import Client

from .types import Options

async def get_client(options: Options) -> Client:
    return await Client.connect(options.target_host, namespace=options.namespace)