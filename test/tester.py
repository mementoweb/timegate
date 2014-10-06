__author__ = 'Yorick Chollet'

import unittest
# from test_server import TestServerSequence

# all files that contains test suites
modules = [
    'test_server'
]


# global test suite
def makesuite():
    st = unittest.TestSuite()
    for t in modules:
        try:
            # loads the module and its variables.
            mod = __import__(t, globals(), locals(), ['suite'])
            suitefn = getattr(mod, 'suite')
            # adds all tests to the suite.
            st.addTest(suitefn())
        except (ImportError, AttributeError):
            st.addTest(unittest.defaultTestLoader.loadTestsFromName(t))
    return st


def run():
    # suite = unittest.TestLoader().loadTestsFromTestCase(TestServerSequence)
    suite = makesuite()
    unittest.TextTestRunner(verbosity=2).run(suite)


if __name__ == '__main__':
    run()