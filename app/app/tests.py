from django.test import TestCase

from app.calc import add


class CalcTest(TestCase):

    def test_add_numbers(self):
        """
        Test that two numbers asre added together
        """
        self.assertEqual(add(3, 5), 8)
