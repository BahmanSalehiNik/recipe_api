import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

import json

RECIPES_URL = reverse('recipe:recipe-list')


def image_upload_url(recipe_id):
    """Return recipe image upload url"""
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


def detail_url(recipe_id):
    """Return recipe detail url"""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def sample_tag(user, name='Test tag'):
    """Create and return a sample tag"""
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='milk'):
    """Create and return a sample ingredient"""
    return Ingredient.objects.create(user=user, name=name)


def sample_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        'title': 'sample_r',
        'time_minutes': 5,
        'price': 32.55
    }
    defaults.update(params)
    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        res = self.client.get(RECIPES_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('test@test.ir',
                                                    'passTest')
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes"""
        sample_recipe(user=self.user, title='steak')
        sample_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_limited_to_user(self):

        new_user = get_user_model().objects.create_user('newuser@test.ir',
                                                        'pass2@Test')
        sample_recipe(user=new_user, title='new_sample')
        recipe = sample_recipe(user=self.user, title='test')

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user).order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)

    def test_view_recipe_detail(self):
        """Test viewing a recipe detail"""
        recipe = sample_recipe(user=self.user)

        tag = sample_tag(user=self.user)
        ingredient = sample_ingredient(user=self.user)

        recipe.tags.add(tag)
        recipe.ingredients.add(ingredient)

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        """Test creating recipe"""
        payload = {
            'title': 'cheeseCacke',
            'time_minutes': 25,
            'price': 4.34
        }
        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])
        serializer = RecipeSerializer(recipe)
        for key in payload.keys():
            self.assertEqual(str(payload[key]), str(serializer.data[key]))

    def test_create_recipe_with_ingredients(self):
        """Test creating a recipe with ingredients"""
        ingredient_1 = sample_ingredient(user=self.user, name='Meat')
        ingredient_2 = sample_ingredient(user=self.user, name='Mushroom')
        payload = {
            'title': ' lunch',
            'time_minutes': 34,
            'price': 78.99,
            'ingredients': [ingredient_1.id, ingredient_2.id]
        }
        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])
        ingredients = recipe.ingredients.all()

        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient_1, ingredients)
        self.assertIn(ingredient_2, ingredients)

    def test_created_recipe_with_tags(self):

        tag_1 = sample_tag(user=self.user, name='Steak')
        tag_2 = sample_tag(user=self.user, name='Dinner')
        payload = {
            'title': 'Sample recipe',
            'tags': [tag_1.id, tag_2.id],
            'time_minutes': 45,
            'price': 134.44,
        }

        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        tags = recipe.tags.all()

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag_1, tags)
        self.assertIn(tag_2, tags)

    def test_partial_updating_recipe(self):
        """Test updating a recipe with patch"""
        tag_1 = sample_tag(user=self.user, name='Barbeque')
        ingredient_1 = sample_ingredient(user=self.user, name="Meat")

        payload = {
            'title': 'Barbeque kobab',
            'time_minutes': 45,
            'price': 100.00,
            'tags': [tag_1.id],
            'ingredients': [ingredient_1.id]
        }

        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        payload_update = {'title': 'New kobab'}
        url = detail_url(res.data['id'])
        res_update = self.client.patch(url, payload_update)

        recipe = Recipe.objects.get(id=res.data['id'])
        recipe.refresh_from_db()

        self.assertEqual(recipe.title, payload_update['title'])
        tags = recipe.tags.all()
        self.assertEqual(len(tags), 1)
        self.assertIn(tag_1, tags)

    def test_full_update_recipe(self):
        """Test fully updating a recipe"""
        recipe = sample_recipe(user=self.user, title='soup')
        tag_1 = sample_tag(user=self.user, name='picnic')
        ingredient_1 = sample_ingredient(user=self.user, name='vegetables')
        payload = {
            'title': 'Ghormeh',
            'time_minutes': 180,
            'price': 35.00,
            'tags': [tag_1.id],
            'ingredients': [ingredient_1.id]
        }
        url = detail_url(recipe.id)
        self.client.put(url, payload)
        recipe.refresh_from_db()

        serializer = RecipeSerializer(recipe)
        self.assertEqual(payload['title'], serializer.data['title'])


class RecipeImageUploadTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'test@test.ir',
            'TestPass'
        )
        self.client.force_authenticate(self.user)
        self.recipe = sample_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image_to_recipe(self):
        """Test uploading an image to recipe"""
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', (10, 10))
            img.save(ntf, format='JPEG')
            ntf.seek(0)
            res = self.client.post(url, {'image': ntf}, format='multipart')

            self.recipe.refresh_from_db()
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertIn('image', res.data)
            self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image"""
        url = image_upload_url(self.recipe.id)
        res = self.client.post(url, {'image': 'data'}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_recipes_by_tags(self):
        """Test returning recipes by specific tags"""
        recipe_1 = sample_recipe(user=self.user, title='Wine')
        recipe_2 = sample_recipe(user=self.user, title='Mohito')
        tag_1 = sample_tag(user=self.user, name='Alcohol')
        tag_2 = sample_tag(user=self.user, name='Vegan')
        recipe_1.tags.add(tag_1)
        recipe_2.tags.add(tag_2)
        recipe_3 = sample_recipe(user=self.user, title='Fish')

        res = self.client.get(
            RECIPES_URL,
            {'tags' :f'{tag_1.id}, {tag_2.id}'}
        )

        serializer_1 = RecipeSerializer(recipe_1)
        serializer_2 = RecipeSerializer(recipe_2)
        serializer_3 = RecipeSerializer(recipe_3)

        self.assertIn(serializer_1.data, res.data)
        self.assertIn(serializer_2.data, res.data)
        self.assertNotIn(serializer_3.data, res.data)

    def test_filtering_recipes_by_ingredients(self):
        """Test filtering recipes by specific ingredients"""
        recipe_1 = sample_recipe(user=self.user, title='Kobab')
        recipe_2 = sample_recipe(user=self.user, title='Vegetable Pizza')
        recipe_3 = sample_recipe(user=self.user, title='Salad')
        ingredient_1 = sample_ingredient(user=self.user, name='Meat')
        ingredient_2 = sample_ingredient(user=self.user, name='Cheese')
        recipe_1.ingredients.add(ingredient_1)
        recipe_2.ingredients.add(ingredient_2)

        res = self.client.get(
            RECIPES_URL,
            {'ingredients': f'{ingredient_1.id}, {ingredient_2.id}'}
        )

        serializer_1 = RecipeSerializer(recipe_1)
        serializer_2 = RecipeSerializer(recipe_2)
        serializer_3 = RecipeSerializer(recipe_3)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer_1.data, res.data)
        self.assertIn(serializer_2.data, res.data)
        self.assertNotIn(serializer_3, res.data)



