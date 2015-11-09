import random


class Config(object):
    pass


def test_setup(f):
    def _wrapped(kls, config):
        return f(kls, config)

    _wrapped.__name__ == f.__name__
    _wrapped.scenario_setup = True
    return _wrapped


def test_teardown(f):
    def _wrapped(kls, config):
        return f(kls, config)

    _wrapped.__name__ = f.__name__
    _wrapped.scenario_teardown = True
    return _wrapped


class test(object):
    def __init__(self, iterations=1):
        self.iterations = iterations

    def __call__(self, f):
        def _wrapped(kls, config):
            return f(kls, config)
        _wrapped.scenario_test = True
        _wrapped.__name__ = f.__name__
        _wrapped.iterations = self.iterations
        return _wrapped

class ExampleScenario(object):
    @test_setup
    def setup(self, config):
        print "Setup called"

    @test_teardown
    def teardown(self, config):
        print "Teardown called"

    @test(iterations=10)
    def foo(self, config):
        print "foo called"

    @test(iterations=20)
    def bar(self, config):
        print "bar called"

    def baz(self):
        pass

p = ExampleScenario()
setup_method, teardown_method = None, None
test_methods = []
for attr_name in dir(p):
    attr = getattr(p, attr_name)
    if callable(attr):
        if hasattr(attr, "iterations"):
            test_methods.extend([attr] * attr.iterations)
        elif hasattr(attr, "scenario_setup"):
            setup_method = attr
        elif hasattr(attr, "scenario_teardown"):
            teardown_method = attr


config = Config()
print setup_method
setup_method(config)
random.shuffle(test_methods)
for meth in test_methods:
    meth(config)
teardown_method(config)
