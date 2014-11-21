import json
import multiprocessing
import time

from neutronclient.v2_0 import client as clientv20

# Possible Flow:
# init
# run_once
# test_scenario
# process_results
# teardown_scenario
# teardown_all

# Ideas:
# * Standard DSL for defining test scenarios
# * Scenarios are strictly ordered test sets
# * A runner receives a scenario, which could be 1 to N tests
# * Tests must define their own validations
# * We may provide unittest2 style validations
# * Whole thing should be containerized or otherwise instantly replaceable
# * Use a decorator syntax ala CommandManager to define tesst with
#   setup+teardown
# * Teardowns must always run and be fault tolerant
#
# I'd like a second, meta-tox piece that does the following:
# * Provides "mutations" for changing configurations on the server
# * Changing the server could be provided by ansible
# * Mutations are things like ConfigMutation, PackageMutation etc
# * ConfigMutation: Changes a neutron.conf variable in a range
# * PackageMutation: Changes a package version in a fixed range, or with a DSL
#   0.1 <-> 0.2 OR $NOW <-> $LATEST (should use distribute semantics

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
    "auth_retries": 10,
    "teardown_retries": 10,
    "service_type": "network",
}


def load_conf(path=None):
    global CONF
    if path:
        with open(path, 'r') as f:
            new_conf = json.load(f)
            CONF.update(new_conf)


def get_client():
    params = {
        "auth_url": CONF["auth_url"],
        "timeout": CONF["timeout"],
        "insecure": CONF["insecure"],
        "auth_strategy": CONF["auth_strategy"],
        "username": CONF["username"],
        "tenant_name": CONF["tenant_name"],
        "service_type": CONF["service_type"]
    }
    auth_strategy = CONF.get("auth_strategy", "keystone")
    if auth_strategy == "keystone":
        params["password"] = CONF["password"]
    elif auth_strategy == "rackspace":
        params["token"] = CONF["password"]
    elif auth_strategy == "noauth":
        params.pop("auth_url")
        params["endpoint_url"] = CONF["endpoint_url"]
        params["token"] = CONF["password"]

    if "region_name" in CONF:
        params["region_name"] = CONF["region_name"]

    client = clientv20.Client(**params)
    return client


def harness(test_method):
    start_time = time.time()
    res = test_method()
    end_time = time.time() - start_time
    return (res[0], res[1], end_time)


def run_tests(runner):
    pool = multiprocessing.Pool(processes=CONF["workers"])

    tests = [pool.apply_async(runner)
             for iteration in xrange(CONF["iterations"])]
    results = [test.get() for test in tests]

    #process_results(results)
