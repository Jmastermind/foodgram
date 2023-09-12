from django.db.models.query import QuerySet
from django_filters import ModelMultipleChoiceFilter
from django_filters.rest_framework import FilterSet, filters

from recipes.models import Recipe, Tag
from users.models import User


class RecipeFilter(FilterSet):
    """
    Django фильтр для фильтрации рецептов.

    Query parameters:
        tags: фильтрация по слагу тега
        author: фильтрация по автору рецепта
        is_favorited: фильтрация по наличию в избранном [bool]
        is_in_shopping_cart: фильтрация по наличию в списке покупок [bool]
    """
    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    author = filters.ModelChoiceFilter(queryset=User.objects.all())
    is_favorited = filters.BooleanFilter(method='filter_favorited')
    is_in_shopping_cart = filters.BooleanFilter(method='filter_shopping_cart')

    def filter_favorited(self, queryset, name, value) -> QuerySet:
        user_id = getattr(self.request.user, 'id', None)
        if value and user_id:
            return queryset.filter(favorite_recipe__user=user_id)
        return queryset

    def filter_shopping_cart(self, queryset, name, value) -> QuerySet:
        user_id = getattr(self.request.user, 'id', None)
        if value and user_id:
            return queryset.filter(cart_recipe__user=self.request.user)
        return queryset

    class Meta:
        model = Recipe
        fields = (
            'tags',
            'author',
        )
