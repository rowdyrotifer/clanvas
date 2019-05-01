import unittest

from tests.config.test_config import TestConfigParser
from tests.regression.test_regression import TestRegression


if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(TestRegression())
    suite.addTest(TestConfigParser())
    unittest.TextTestRunner().run(suite)
