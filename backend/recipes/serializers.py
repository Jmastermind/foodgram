from collections import OrderedDict

from django.shortcuts import get_object_or_404
from drf_base64.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import ValidationError

from recipes.models import Ingredient, IngredientAmount, Recipe, Tag
from users.models import User
from users.serializers import UsersSerializer


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов блюд."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientAmountSerializer(serializers.ModelSerializer):
    """Сериализатор для колличества ингредиентов в рецепте."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit',
    )

    class Meta:
        model = IngredientAmount
        fields = ('id', 'name', 'measurement_unit', 'amount')


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    class Meta:
        model = Tag
        fields = '__all__'


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для сокращенного отображения рецептов."""

    image = serializers.ReadOnlyField(source='image.url')

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('__all__',)


class RecipeSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для рецептов."""

    author = UsersSerializer()
    tags = TagSerializer(many=True)
    ingredients = IngredientAmountSerializer(
        many=True,
        read_only=True,
        source='ingredient_amounts',
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_is_favorited(self, recipe: Recipe) -> bool:
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return user.favorite_user.filter(recipe=recipe).exists()

    def get_is_in_shopping_cart(self, recipe: Recipe) -> bool:
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return user.cart_owner.filter(recipe=recipe).exists()


class IngredientAmountWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для модицикации ингридиентов в рецептах."""

    id = serializers.IntegerField(write_only=True)

    class Meta:
        model = IngredientAmount
        fields = ('id', 'amount')


class RecipeSerializerModify(RecipeSerializer):
    """Сериализатор для модицикации рецептов."""

    image = Base64ImageField(default='recipes/default.png')
    author = UsersSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    ingredients = IngredientAmountWriteSerializer(many=True)

    def create_ingredient_amount(
        self,
        ingredients: list[dict],
        recipe: Recipe,
    ) -> None:
        IngredientAmount.objects.bulk_create(
            [
                IngredientAmount(
                    recipe=recipe,
                    ingredient=get_object_or_404(
                        Ingredient,
                        id=ingredient.get('id'),
                    ),
                    amount=ingredient.get('amount'),
                )
                for ingredient in ingredients
            ],
        )

    def validate_ingredients(self, ingredients: list[dict]) -> list[dict]:
        if not ingredients:
            raise ValidationError({'ingredients': 'Ингредиенты отсутствуют'})
        unique_ingredients = []
        for ingredient in ingredients:
            ing_id = ingredient.get('id')
            if ing_id is None:
                raise ValidationError(
                    {'ingredients': 'Отсутствует id ингредиента'},
                )
            if not Ingredient.objects.filter(id=ing_id).exists():
                raise ValidationError(
                    {
                        'ingredients': f'Ингредиента не существует: {ing_id}',
                    },
                )
            if ing_id in unique_ingredients:
                raise ValidationError(
                    {'ingredients': f'Ингредиент не уникален: {ing_id}'},
                )
            unique_ingredients.append(ing_id)
            if int(ingredient.get('amount')) < 1:  # type: ignore
                raise ValidationError(
                    {'ingredients': f'Кол-во ингредиента {ing_id} меньше 1'},
                )
        return ingredients

    def validate_tags(self, tags_ids: list[int]) -> list[int]:
        if not tags_ids:
            raise ValidationError({'tags': 'Теги отсутствуют'})
        if len(tags_ids) != len(set(tags_ids)):
            raise ValidationError({'tags': 'Теги не должны повторяться'})
        return tags_ids

    def validate(self, attrs: dict) -> dict:
        author = self.context.get('request').user
        if self.instance:
            if (
                Recipe.objects.filter(
                    author=author,
                    name=attrs.get('name'),
                )
                .exclude(pk=self.instance.pk)
                .exists()
            ):
                raise ValidationError({'error': 'Такой рецепт у вас уже есть'})
        else:
            if Recipe.objects.filter(
                author=author,
                name=attrs.get('name'),
            ).exists():
                raise ValidationError({'error': 'Такой рецепт у вас уже есть'})
        return attrs

    def create(self, validated_data: dict) -> Recipe:
        tags: list[Tag] = validated_data.pop('tags')
        ingredients: list[dict] = validated_data.pop('ingredients')
        validated_data.update(author=self.context.get('request').user)
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredient_amount(ingredients, recipe)
        return recipe

    def update(self, recipe: Recipe, validated_data: dict) -> Recipe:
        tags: list[Tag] = validated_data.pop('tags', None)
        ingredients: list[dict] = validated_data.pop('ingredients', None)
        recipe = super().update(recipe, validated_data)
        if tags:
            recipe.tags.clear()
            recipe.tags.set(tags)
        if ingredients:
            recipe.ingredients.clear()
            self.create_ingredient_amount(ingredients, recipe)
        return recipe

    def to_representation(self, instance: Recipe) -> OrderedDict:
        request = self.context.get('request')
        return RecipeSerializerRetrieve(
            instance,
            context={'request': request},
        ).data


class RecipeSerializerRetrieve(RecipeSerializer):
    """Сериализатор для отображения рецептов."""

    image = serializers.ReadOnlyField(source='image.url')

    class Meta(RecipeSerializer.Meta):
        read_only_fields = ('__all__',)


class UserSubscribeSerializer(UsersSerializer):
    """Сериализатор для подписок пользователя."""

    recipes = ShortRecipeSerializer(many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta(UsersSerializer.Meta):
        fields = UsersSerializer.Meta.fields + (  # type: ignore
            'recipes',
            'recipes_count',
        )

    def get_recipes_count(self, author: User) -> int:
        return author.recipes.count()
