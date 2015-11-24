import sys

import horde

# Possible Flow:
# init
# run_once
# test_scenario
# process_results
# teardown_scenario
# teardown_all


def stress_port():
    # TODO This should be creating the network and subnet for the port
    client = horde.get_client()
    port_dict = {"port": {"network_id": horde.CONF["network_id"]}}
    if horde.CONF["auth_strategy"] == "noauth":
        port_dict["port"]["tenant_id"] = horde.CONF["tenant_name"]

    try:
        port = client.create_port(port_dict)
        p = port["port"]
        if "mac_address" not in p:
            raise Exception("No MAC address found")
        if "fixed_ips" not in p:
            raise Exception("No MAC address found")
        for ip in p["fixed_ips"]:
            if "subnet_id" not in ip:
                raise Exception("No subnet found")
            if "ip_address" not in ip:
                raise Exception("No ip_address found")
            if len(ip["subnet_id"]) == 0:
                raise Exception("Subnet is empty")
            if len(ip["ip_address"]) == 0:
                raise Exception("IP address is empty")
    except Exception as e:
        return (False, e)
    return (True, port)


def teardown(port):
    # This isn't working perfectly, and we need to find out why

    teardown_retries = 0
    # auth_retries = 0
    while True:
        try:
            client = horde.get_client()
            if isinstance(port, dict):
                client.delete_port(port["port"]["id"])
            break
        # This needs to break out unless it's auth
        # except neutronclient.Exception:
        #   continue
        #   auth_retries += 1
        except Exception as e:
            teardown_retries += 1
            if teardown_retries == horde.CONF["teardown_retries"]:
                print e
                break


def process_results(res):
    tests = [pool.apply_async(stress_port)
             for iteration in xrange(CONF["iterations"])]
    results = [test.get() for test in tests]
    ports_pass = 0
    ports_fail = 0

    min_time, max_time = None, None
    total_time = 0
    for success, result, end_time in results:
        if not max_time:
            max_time = run_time
            min_time = run_time
        if run_time < min_time:
            min_time = run_time
        if run_time > max_time:
            max_time = run_time
        total_time += run_time

        if success:
            ports_pass += 1
        else:
            ports_fail += 1
            print result

    average = total_time / int(CONF["iterations"])
    stddev_sum = 0
    for success, run_time, result in results:
        stddev_sum += (run_time - average) ** 2
    stddev = math.sqrt(stddev_sum / int(CONF["iterations"]))

    print "Passed:", ports_pass
    print "Failed:", ports_fail
    print "Average:", average
    print "Minimum:", min_time
    print "Maximum:", max_time
    print "Stddev:", stddev
    print "Total time:", time.time() - start_time

    # Would be lovely to get Neutron to tell on itself: how many
    # times did it retry giving us these results, how many of those
    # were policy related, collisions with other procs, and deadlocks?
    #
    # Ways this could work:
    #
    # Send a POST to an admin extension -> stats mode
    # Things we care about honor stats mode, pushing data into memory
    # Send a DELETE to admin extension -> stats mode is off
    # GET on the extension -> Get stat dump

    # Would also be lovely to have an exhaust subnet test, see how far it goes,
    # see if it actually generated *all* the IPs in the subnet, and so on.

    teardown_results = [pool.apply_async(teardown, (p,))
                        for s, t, p in results if p]
    print "Issued all teardowns, waiting for final cleanup..."
    for res in teardown_results:
        res.wait()


if __name__ == "__main__":
    path = None
    if len(sys.argv) > 1:
        path = sys.argv[1]
    horde.load_conf(path)
    horde.run_tests(runner='', process_results='', teardown='')
