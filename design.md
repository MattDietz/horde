Why this exists:
I considered extending my old repo here: https://github.com/Cerberus98/fusion/tree/master/fusion

However, unit testing is about vetting some piece of functionality one time,
in isolation (i.e. a unit) and then returning success or failure. I want this
framework to be more flexible, allowing one to test individual pieces of
functionality en-masse, multiple times (say, to vet N nodes behind a load
balancer) or to prove the performance of a given piece of software.

Another thing I want is the ability to analyze the results in aggregate,
and emit statistics about the run, like the mean, median and standard
deviation

Finally, I would say the design goal of Horde is to provide an easy,
transparent means for rapid endpoint verification as well as rapidly apply
changes to any endpoint that supports non-blocking I/O, similiar to how
Ansible concurrently modifies hosts.

Ideas:
* Standard DSL for defining test scenarios
* Optionally, a StrictScenario, which are strictly ordered test sets
* A runner receives a scenario, which could be 1 to N tests
* Tests must define their own validations
* We may provide unittest2 style validations
* Whole thing should be containerized or otherwise instantly replaceable
* Use a decorator syntax ala CommandManager to define tests with
  setup+teardown
* Teardowns must always run and be fault tolerant
* A customer Job builder hook that bypasses parts of the discovery step, so can do more
  Map-Reduce style things


Test Scenarios
=======================

Test scenarios look just like TestSuites in unittest. The difference is that individual tests in a scenario can be run more than once. I think it should also be possible to specify the number of iterations via command line or configuration file.

Ideally, all of these should be valid:

class PortScenarios(horde.Scenario):
    @horde.setup
    def setup(self, config):
        # called once per scenario. I like the use of a decorator for setup
        # because it (sort of) bypasses the chicken and egg problem where
        # you want to test the functionality of a specific class but first
        # you need to create an instance of that object. So where does it go?
        # You can put it in the setup, but the setup implies stuff thats tested
        # or outside the scope of the tests being run. Alternative, you can put
        # it in each test method and tear it down at the end (and sometimes this
        # is the right answer) but 
        pass
    
    @horde.teardown
    def teardown(self, config):
        # called once per scenario
        pass

    def process_results(self, results):
        # called once per scenario, is passed result objects
        # from every other iteration of the test
        pass

    @horde.test()
    def list_ports(self, config):
        pass

    @horde.test(iterations=100):
    def create_provider_port(self, config):
        # You will be responsible for cleanup, so ensuring the port ids
        # are passed back in the the result object so that they can be
        # deleted in the teardown is advised.
        pass

    @horde.test(iterations=horde.config.get("isolated_ports"))
    def create_isolated_port(self, config):
        pass


What I want to have happen here is the scenarios are "flattened" into a single list of tests that we can map amongst all the processes in the process pool. To start, horde would fire off the setup method *exactly once* and then aggregate a randomized flattened list as a collection of "jobs" and said jobs would be run by the children in the pool.

So, in the above example lets say isolated_ports==100. We call setup. Then, horde finds all the decorated lists and figures out there are 201 things to run. Additionally, the process count is set to 4. Horde creates 4 jobs of 50, 50, 50 and 51 tests to run and applies those jobs to the multiprocessing pool.

Config Setup and Teardown
========================

Getting data from the setup down to the Job. We can store it in the global config but we should make the config read only after a certain point

How about this: we pass a config object to the setup method that secretly gives namespaced names to things set through it and hides that all from the developer. Example:

config = horde.config.ConfigReadWrite("PortScenarios")

def setup(self, config):
    # This config object was initialized
    port = port_create(...)
    config.set("port_id", port["id")

In the config, this variable is actually called "PortScenarios.port_id". When the Job is created, it is given a ConfigReader() object. Meanwhile, each test will have an member variable saying which Scenario it is actually part of. The given test only sees the config object it is allowed to see, so any config.get automatically namespaces the variable.
    
Test Runners
===============

ProcessRunner - a runner that executes the test 1:1 within a child process, waiting until the termination of the test
EventletRunner - A runner that executes all tests in an eventlet pool of configurable size, waiting until the termination of each test
MultiventletRunner - A runner that spawns multiple child processes, each with their own eventlet pool, and subdivides the work amongst all of them
in an attempt to maximize concurrency

Discovery
=========
Tests can be discovered one of two ways:

* Passing an explicit path on the command line
* Recursive directory search, identifying all subclasses of HordeScenario


Terms
=============
* Jobs are collections of Tasks that must be executed in any order
* Tasks are units of work that must be performed
* Tests are an alias for Tasks
* TaskSets are collections of tasks that will be run in a specific order. They appear to be equivalent to a single task to the test runner
* The JobBuilder is a tool to create Jobs without using the Task or Test syntax. One can use the JobBuilder to assemble collections of work for which you want explicit inputs. For example:
    Say you wanted to insert all IP addresses from a /8 into the database as quickly as possible.

    import netaddr

    ip_net = netaddr.IPNetwork("10.0.0.0/8")
    def insert_ip(ip, config):
        ...
        do something
        ...

    jobs = horde.build_jobs(ip_net, subsets=NUM_PROCESSSES, shuffle=False)
    horde.run(jobs)

    
