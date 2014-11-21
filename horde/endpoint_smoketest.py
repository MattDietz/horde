import sys
import traceback

import horde


# TODO other tests
# Create v6 network, subnet and ports
# Ensure ports have MAC addresses
# Subnet size bounds
# Security Groups.*


def test_create(client, res, body):
    func = getattr(client, "create_%s" % res)
    if func:
        try:
            return func(body)
        except Exception as e:
            print "Couldn't create %s | %s" % (res, traceback.format_exc(e))
            raise


def test_list(client, list_label, orig_res):
    func = getattr(client, "list_%s" % list_label)
    if func:
        try:
            res_list = func()
        except Exception as e:
            print "Couldn't list %s | %s" % (list_label,
                                             traceback.format_exc(e))
            raise
    res_found = False
    for res in res_list[list_label]:
        if res["id"] == orig_res["id"]:
            res_found = True
            break

    if not res_found:
        raise Exception("Created %s missing from list call" % list_label)


def test_show(client, res, orig_res):
    func = getattr(client, "show_%s" % res)
    if func:
        try:
            res_show = func(orig_res["id"])
        except Exception as e:
            print "Couldn't show %s | %s" % (res, traceback.format_exc(e))
            raise

    if orig_res["id"] != res_show[res]["id"]:
        print "Mismatch between shown and posted %s IDs" % res


def endpoint_test():
    client = horde.get_client()
    net_dict = {"network": {"name": "testnetwork"}}

    def _rescue_nil(func, *args):
        try:
            func(*args)
        except Exception as e:
            print "Delete failed", traceback.format_exc(e)

    try:
        net_resource = test_create(client, "network", net_dict)
        subnet_dict = {"subnet": {"network_id": net_resource["network"]["id"],
                                  "cidr": "192.168.0.0/24",
                                  "ip_version": 4}}
        port_dict = {"port": {"network_id": net_resource["network"]["id"]}}
        subnet_resource = test_create(client, "subnet", subnet_dict)
        port_resource = test_create(client, "port", port_dict)

        test_list(client, "ports", port_resource["port"])
        test_list(client, "subnets", subnet_resource["subnet"])
        test_list(client, "networks", net_resource["network"])

        test_show(client, "port", port_resource["port"])
        test_show(client, "subnet", subnet_resource["subnet"])
        test_show(client, "network", net_resource["network"])

        print "Network, subnet and port created"
    except Exception as e:
        print e
    finally:
        _rescue_nil(client.delete_port, port_resource["port"]["id"])
        _rescue_nil(client.delete_subnet, subnet_resource["subnet"]["id"])
        _rescue_nil(client.delete_network, net_resource["network"]["id"])
        print "Finished deleteing network, subnet and port"


if __name__ == "__main__":
    path = None
    if len(sys.argv) > 1:
        path = sys.argv[1]
    horde.load_conf(path)
    horde.run_tests(endpoint_test)
