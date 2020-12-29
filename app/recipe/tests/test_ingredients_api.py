from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe

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

    def test_create_ingredients_successfully(self):
        """Test that ingredients are created successfully"""
        payload = {'name': 'water'}
        res = self.client.post(INGREDIENTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        exists = Ingredient.objects.filter(
                user=self.user,
                name=payload['name']
                ).exists()
        self.assertTrue(exists)

    def test_create_ingredients_unauthorized_user(self):
        """Test that unauthorized user cannot create ingredients"""
        new_user = get_user_model().objects.create_user(email='new_user@test.ir', password='newPass')
        new_client = APIClient()
        #new_client.force_authenticate(new_user)

        res = new_client.post(INGREDIENTS_URL, {'name': 'Orange'})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        #Ingredient.objects.create(user=new_user, name='Orange')
        #exists = Ingredient.objects.filter(user=new_user, name='Orange').exists()
        #self.assertFalse(exists)

    def test_create_ingredients_invalid(self):
        """Test that ingredients with invalid data are not created"""
        payload = {'name': ''}
        res = self.client.post(INGREDIENTS_URL,payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieving_ingredients_assigned_to_recipe(self):
        """Test filtering ingredients assigned to recipe"""
        ingredient_1 = Ingredient.objects.create(user=self.user, name='Milk')
        ingredient_2 = Ingredient.objects.create(user=self.user, name='Salt')
        recipe = Recipe.objects.create(
            user=self.user,
            time_minutes=23,
            price=34.00,
            title='Breakfast'
        )
        recipe.ingredients.add(ingredient_1)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})
        serializer_1 = IngredientSerializer(ingredient_1)
        serializer_2 = IngredientSerializer(ingredient_2)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer_1.data, res.data)
        self.assertNotIn(serializer_2.data, res.data)

    def test_retrieving_ingredients_assigned_unique(self):
        """Test filtering ingredients by assigned returns unique items"""
        ingredient = Ingredient.objects.create(user=self.user, name='Meat')
        Ingredient.objects.create(user=self.user, name='Chicken')

        recipe_1 = Recipe.objects.create(
            user=self.user,
            title='Dinner',
            time_minutes=35,
            price=56.00
        )

        recipe_2 = Recipe.objects.create(
            user=self.user,
            title='Pizza',
            time_minutes=45,
            price=34.00
        )

        recipe_1.ingredients.add(ingredient)
        recipe_2.ingredients.add(ingredient)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})
        self.assertEqual(len(res.data), 1)