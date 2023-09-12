from django.db import IntegrityError
from django.urls import reverse
from mixer.backend.django import mixer
from rest_framework import status
from rest_framework.test import APITestCase

from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from users.models import User


class IngredientsTests(APITestCase):
    def test_ingredient_empty_field(self) -> None:
        try:
            Ingredient.objects.create(name='', measurement_unit='kg')
        except IntegrityError as err:
            self.assertEqual(
                err.__str__(),
                'CHECK constraint failed: recipes_ingredient_name_empty',
            )

    def test_ingredient_list(self) -> None:
        ing = mixer.cycle(8).blend(
            Ingredient,
            name=(
                name
                for name in (
                    'Egg',
                    'salt',
                    'salmon',
                    'mango',
                    'sugar',
                    'chocolate',
                    'apple',
                    'Hennessy',
                )
            ),
        )
        for i in ing:
            i.full_clean()
            i.save()

        url = reverse('recipes:ingredients-list')
        response = self.client.get(url, format='json')
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.json(),
        )

        response = self.client.get(url, {'name': 's'}, format='json')
        self.assertEqual(
            len(response.json()),
            4,
        )

    def test_ingredient_detail(self) -> None:
        i = mixer.blend(Ingredient, name=' salmon')
        i.full_clean()
        i.save()
        url = reverse('recipes:ingredients-detail', args=(1,))
        response = self.client.get(url, format='json')
        self.assertEqual(
            response.json()['name'],
            'Salmon',
        )

    def test_ingredient_cant_post(self) -> None:
        user = mixer.blend(User)
        self.client.force_authenticate(user)
        url = reverse('recipes:ingredients-list')
        data = {
            'name': '',
            'measurement_unit': '',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )


class TagTests(APITestCase):
    def test_tag_empty_field(self) -> None:
        try:
            Tag.objects.create(name='', color='#49B64E', slug='slug')
        except IntegrityError as err:
            self.assertEqual(
                err.__str__(),
                'CHECK constraint failed: recipes_tag_name_empty',
            )

    def test_tag_list(self) -> None:
        mixer.cycle(3).blend(Tag)
        url = reverse('recipes:tags-list')
        response = self.client.get(url, format='json')
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.json(),
        )

    def test_tag_detail(self) -> None:
        mixer.blend(Tag)
        url = reverse('recipes:tags-detail', args=(1,))
        response = self.client.get(url, format='json')
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.json(),
        )


class RecipeTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_get_recipe_list(self) -> None:
        mixer.blend(Recipe)
        url = reverse('recipes:recipes-list')
        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.json(),
        )
        self.assertEqual(
            response.json()['count'],
            1,
        )

    def test_recipe_list(self) -> None:
        tags = mixer.cycle(8).blend(
            Tag,
            slug=(
                slug
                for slug in (
                    'egg',
                    'salt',
                    'salmon',
                    'mango',
                    'sugar',
                    'chocolate',
                    'apple',
                    'Hennessy',
                )
            ),
        )
        mixer.cycle(8).blend(Recipe, tags=(tag for tag in tags))
        url = reverse('recipes:recipes-list')
        response = self.client.get(url, {'tags': 'egg'})
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.json(),
        )
        self.assertEqual(
            response.json()['count'],
            1,
        )

    def test_recipe_detail(self) -> None:
        mixer.blend(Recipe)
        url = reverse('recipes:recipes-detail', args=(1,))
        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.json(),
        )

    def test_recipe_create(self) -> None:
        mixer.cycle(2).blend(Ingredient)
        mixer.cycle(2).blend(Tag)
        user = mixer.blend(User)
        self.client.force_authenticate(user)
        url = reverse('recipes:recipes-list')
        data = {
            'ingredients': [{'id': 1, 'amount': 2}, {'id': 2, 'amount': 1}],
            'tags': [2, 1],
            'image': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg==',  # noqa: E501
            'name': 'Fried Chicken',
            'text': 'Must be tasty',
            'cooking_time': 2,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            response.json(),
        )
        self.assertEqual(Recipe.objects.count(), 1)

    def test_recipe_create_no_image(self) -> None:
        mixer.cycle(2).blend(Ingredient)
        mixer.cycle(2).blend(Tag)
        user = mixer.blend(User)
        self.client.force_authenticate(user)
        url = reverse('recipes:recipes-list')
        data = {
            'ingredients': [{'id': 1, 'amount': 2}, {'id': 2, 'amount': 1}],
            'tags': [2, 1],
            'name': 'Fried Chicken',
            'text': 'Must be tasty',
            'cooking_time': 2,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            response.json(),
        )
        self.assertEqual(Recipe.objects.count(), 1)
        self.assertEqual(
            response.json().get('image'),
            '/media/recipes/default.png',
        )

    def test_recipe_update(self) -> None:
        mixer.cycle(2).blend(Ingredient)
        mixer.cycle(2).blend(Tag)
        user = mixer.blend(User)
        mixer.blend(Recipe, author=user)
        self.client.force_authenticate(user)
        url = reverse('recipes:recipes-detail', args=(1,))
        data = {
            'ingredients': [{'id': 1, 'amount': 2}, {'id': 2, 'amount': 1}],
            'tags': [2, 1],
            'image': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg==',  # noqa: E501
            'name': 'Fried Chicken',
            'text': 'Must be tasty',
            'cooking_time': 2,
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.json(),
        )
        self.assertEqual(Recipe.objects.count(), 1)

    def test_recipe_delete(self) -> None:
        user = mixer.blend(User)
        mixer.blend(Recipe, author=user)
        self.client.force_authenticate(user)
        url = reverse('recipes:recipes-detail', args=(1,))
        response = self.client.delete(url)
        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )
        self.assertEqual(Recipe.objects.count(), 0)

    def test_recipe_to_favorite(self) -> None:
        user = mixer.blend(User)
        mixer.blend(Recipe)
        self.client.force_authenticate(user)
        url = reverse('recipes:recipes-favorite', args=(1,))
        response = self.client.post(url)
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(Favorite.objects.count(), 1)

    def test_recipe_remove_from_favorite(self) -> None:
        user = mixer.blend(User)
        recipe = mixer.blend(Recipe)
        Favorite.objects.create(user=user, recipe=recipe)
        self.client.force_authenticate(user)
        url = reverse('recipes:recipes-favorite', args=(1,))
        response = self.client.delete(url)
        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )
        self.assertEqual(Favorite.objects.count(), 0)

    def test_recipe_to_cart(self) -> None:
        user = mixer.blend(User)
        mixer.blend(Recipe)
        self.client.force_authenticate(user)
        url = reverse('recipes:recipes-shopping-cart', args=(1,))
        response = self.client.post(url)
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(ShoppingCart.objects.count(), 1)

    def test_recipe_remove_from_cart(self) -> None:
        user = mixer.blend(User)
        recipe = mixer.blend(Recipe)
        ShoppingCart.objects.create(user=user, recipe=recipe)
        self.client.force_authenticate(user)
        url = reverse('recipes:recipes-shopping-cart', args=(1,))
        response = self.client.delete(url)
        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )
        self.assertEqual(ShoppingCart.objects.count(), 0)
