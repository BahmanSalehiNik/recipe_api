from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient

from recipe.serializers import IngredientSerializer


INGREDIENTS_URL = reverse('recipe:ingredient-list')


class PublicIngredientApiTest(TestCase):
    """Test the publicly available ingredients API"""

    def SetUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test login is required to access the endpoint"""
        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientApiTest(TestCase):
    """Test the private ingredients API"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            'test@test.ir',
            'TestPass'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients_list(self):
        """Test retrieving a list of ingridients"""
        Ingredient.objects.create(user=self.user, name='french fries')
        Ingredient.objects.create(user=self.user,name='Milk')

        res = self.client.get(INGREDIENTS_URL)
        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredient_limited_to_user(self):
        """Test that Ingredients returned are for the authenticated user"""
        new_user = get_user_model().objects.create_user('new@new.ir', 'NewPass')

        Ingredient.objects.create(user=new_user, name='pepper')
        ingredient = Ingredient.objects.create(user=self.user, name='ginger')

        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertIn(res.data[0]['name'], ingredient.name)
