import json
import multiprocessing
import sys

from neutronclient.v2_0 import client as clientv20


CONF = {
    "auth_url": "http://127.0.0.1:5000/v2.0",
    "timeout": 120,
    "insecure": True,
    "auth_strategy": "keystone",
    "username": "nova",
    "password": "nova",
    "tenant_name": "nova",
    "workers": 50,
    "iterations": 500,
    "network_id": "4eaaac49-a69f-41f0-a454-ea64334c7d60",
    "auth_retries": 10
}


def load_conf(path=None):
    global CONF
    if path:
        with open(path, 'r') as f:
            new_conf = json.load(f)
            CONF.update(new_conf)


def _get_client():
    params = {
        'auth_url': CONF["auth_url"],
        'timeout': CONF["timeout"],
        'insecure': CONF["insecure"],
        'auth_strategy': CONF["auth_strategy"],
        'username': CONF["username"],
        'tenant_name': CONF["tenant_name"],
    }
    auth_strategy = CONF.get("auth_strategy", "keystone")
    if auth_strategy == "keystone":
        params["password"] = CONF["password"]
    elif auth_strategy == "rackspace":
        params["token"] = CONF["password"]

    for retry in xrange(int(CONF["auth_retries"])):
        try:
            client = clientv20.Client(**params)
            return client
        except Exception:
            continue

    print "Could not successfully authenticate!"


def delete_port(port):
    # This isn't working perfectly, and we need to find out why
    client = _get_client()
    if isinstance(port, dict):
        client.delete_port(port["id"])


def run_tests():
    pool = multiprocessing.Pool(processes=CONF["workers"])

    client = _get_client()
    ports = client.list_ports(network_id=[CONF["network_id"]])

    print "Found %d ports" % len(ports["ports"])
    teardown_results = [pool.apply_async(delete_port, (p, ))
                        for p in ports["ports"]]

    print "Spawned all deletes, waiting for completion..."
    for res in teardown_results:
        res.wait()


if __name__ == "__main__":
    path = None
    if len(sys.argv) > 1:
        path = sys.argv[1]
    load_conf(path)
    run_tests()
