from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe

from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')


class PublicTagsApiTests(TestCase):
    """Test the publicly available tags API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retrieving tags"""
        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTest(TestCase):
    """Test the authorized user tags API"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            'test@test.ir',
            'testPass'
        )

        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test retrieving tags"""
        Tag.objects.create(user=self.user, name='veg')
        Tag.objects.create(user=self.user, name='stake')

        res = self.client.get(TAGS_URL)
        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test that tags returned are for the authenticated user"""
        new_user = get_user_model().objects.create_user(
            'newtest@test.ir',
            'passTest'
        )

        Tag.objects.create(user=new_user, name='pizza')
        tag = Tag.objects.create(user=self.user, name='pasta')

        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)

        #exists = Tag.objects.filter(user=new_user, name='pizza').exists()
        #self.assertFalse(exists)

    def test_create_tag_successful(self):
        """Test creating a new tag"""
        payload = {'name': 'Test tag'}
        self.client.post(TAGS_URL, payload)

        exists = Tag.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()
        self.assertTrue(exists)

    def test_create_tag_invalid(self):
        """Test creating a new tag with invalid payload"""
        payload = {'name': ''}
        res = self.client.post(TAGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_tags_assigned_to_recipes(self):
        """Test filtering tags by those assigned to recipes"""
        tag_1 = Tag.objects.create(user=self.user, name='Lunch')
        tag_2 = Tag.objects.create(user=self.user, name='Dinner')
        recipe = Recipe.objects.create(
            user=self.user,
            title='Stake',
            time_minutes=45,
            price=300.00,
        )
        recipe.tags.add(tag_1)
        res = self.client.get(TAGS_URL, {'assigned_only': 1})
        serializer_1 = TagSerializer(tag_1)
        serializer_2 = TagSerializer(tag_2)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer_1.data, res.data)
        self.assertNotIn(serializer_2.data, res.data)

    def test_retrieve_tags_assigned_unique(self):
        """Test filtering tags by assigned returns unique items"""
        tag = Tag.objects.create(user=self.user, name='Breakfast')
        Tag.objects.create(user=self.user, name='Lunch')

        recipe_1 = Recipe.objects.create(
            user=self.user,
            title='IceCream',
            time_minutes= 5,
            price=4.00
        )

        recipe_2 = Recipe.objects.create(
            user=self.user,
            title='Kobab',
            time_minutes=30,
            price=50.00
        )

        recipe_1.tags.add(tag)
        recipe_2.tags.add(tag)

        res = self.client.get(TAGS_URL,{'assigned_only': 1})

        self.assertEqual(len(res.data), 1)