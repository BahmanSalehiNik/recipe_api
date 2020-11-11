from django.test import TestCase
from django.contrib.auth import get_user_model


class ModelTests(TestCase):

    def test_create_user_with_email_seccessful(self):
        """ Test creating a new user with an email is successful"""
        email = 'test@kardan.ir'
        password = "test_123"
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Tests the email for a user is normalized"""
        email = "b123@TEST.IR"
        user = get_user_model().objects.create_user(email, '123TTT')

        self.assertEqual(user.email, email.lower())

    def test_new_user_invalid_email(self):
        """Test creating user with no email raises error"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, 'test')

    def test_create_new_super_user(self):
        """Test creating a new superuser"""
        user = get_user_model().objects.create_superuser(
            'test@test.com', '2222'
        )
        self. assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

