from django.test import TestCase

from app.calc import add, subtract


class CalcTest(TestCase):

    def test_add_numbers(self):
        """
        Test that two numbers asre added together
        """
        self.assertEqual(add(3, 5), 8)

    def test_subtract_numbers(self):
        """
        Test that variables are subtracted and returned
        """
        self.assertEqual(subtract(8,3), 5)