import random
import unittest
import mock
import os
import time

import xsrfutil

class TestXSRFToken(unittest.TestCase):
    def setUp(self):
        self.secret = os.urandom(100)
        self.entityId = 'entityId'
        self.userId = 'userId'
        self.startTime = time.time()
        self.mockTime = mock.Mock(return_value = self.startTime)
        with mock.patch('time.time', self.mockTime):
            self.xsrfToken = xsrfutil.GetXSRFToken(self.secret, self.entityId, self.userId)

    def testXSRFTokenDecodeValidTime(self):
        # advance time by an amount where we expect the token to be
        # valid.
        validTime = self.startTime + 0.5 * xsrfutil.MAX_XSRF_VALIDITITY_MICROS * 1.0 / 1000 / 1000
        self.mockTime.return_value = validTime
        with mock.patch('time.time', self.mockTime):
            (decodedEntityId, decodedUserId) = xsrfutil.DecodeXSRFToken(self.secret, self.xsrfToken)
        self.assertEquals(decodedEntityId, self.entityId)
        self.assertEquals(decodedUserId, self.userId)

    def testDecodeFailsWhenTimeIsTooLate(self):
        # Expect time to where the token is invalid.
        invalidTime = self.startTime + xsrfutil.MAX_XSRF_VALIDITITY_MICROS * 1.0 / 1000 / 1000 + 1
        self.mockTime.return_value = invalidTime
        exceptionRaised = False
        try:
            with mock.patch('time.time', self.mockTime):
                (decodedEntityId, decodedUserId) = xsrfutil.DecodeXSRFToken(self.secret, self.xsrfToken)
        except xsrfutil.InvalidToken, e:
            exceptionRaised = True
        self.assertTrue(exceptionRaised)

if __name__ == '__main__':
    unittest.main()
