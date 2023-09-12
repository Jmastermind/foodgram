from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models.functions import Length

from users.models import User

models.CharField.register_lookup(Length)


class Ingredient(models.Model):
    """Модель ORM для ингредиентов блюд."""

    name = models.CharField('ингредиент', max_length=200)
    measurement_unit = models.CharField('единицы измерения', max_length=200)

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'ингредиенты'
        ordering = ('name',)
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='%(app_label)s_%(class)s_unique_for_ingredient',
            ),
            models.CheckConstraint(
                check=models.Q(name__length__gt=0),
                name='%(app_label)s_%(class)s_name_empty',
            ),
            models.CheckConstraint(
                check=models.Q(measurement_unit__length__gt=0),
                name='%(app_label)s_%(class)s_measurement_unit_empty',
            ),
        )

    def __str__(self) -> str:
        return self.name

    def clean(self) -> None:
        self.name = self.name.strip().lower().capitalize()
        self.measurement_unit = self.measurement_unit.strip().lower()
        super().clean()


class Tag(models.Model):
    """Модель ORM для тегов рецептов."""

    name = models.CharField(
        'тег',
        max_length=200,
        unique=True,
    )
    color = models.CharField(
        verbose_name='цвет',
        max_length=7,
        unique=True,
        validators=(
            RegexValidator(
                regex=r'^\#[a-zA-Z0-9]{6}$',
                message='Невалидный HEX-код',
            ),
        ),
    )
    slug = models.CharField(
        'слаг',
        max_length=200,
        unique=True,
        validators=(
            RegexValidator(
                regex=r'^[-a-zA-Z0-9_]+$',
                message='Не соответствует формату [a-zA-Z0-9_-]',
            ),
        ),
    )

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'теги'
        ordering = ('name',)
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'color', 'slug'),
                name='%(app_label)s_%(class)s_unique_for_tag',
            ),
            models.CheckConstraint(
                check=models.Q(name__length__gt=0),
                name='%(app_label)s_%(class)s_name_empty',
            ),
            models.CheckConstraint(
                check=models.Q(color__length__gt=0),
                name='%(app_label)s_%(class)s_color_empty',
            ),
            models.CheckConstraint(
                check=models.Q(slug__length__gt=0),
                name='%(app_label)s_%(class)s_slug_empty',
            ),
        )

    def __str__(self) -> str:
        return self.name

    def clean(self) -> None:
        self.name = self.name.strip().lower()
        self.slug = self.slug.strip().lower()
        return super().clean()


class Recipe(models.Model):
    """Модель ORM для рецептов блюд."""

    name = models.CharField('название блюда', max_length=200)
    author = models.ForeignKey(
        User,
        verbose_name='автор',
        on_delete=models.CASCADE,
        related_name='recipes',
    )
    text = models.TextField('описание')
    pub_date = models.DateTimeField('дата публикации', auto_now_add=True)
    image = models.ImageField(
        'изображение блюда',
        upload_to='recipes/',
        blank=True,
        default='recipes/default.png',
    )
    cooking_time = models.IntegerField(
        validators=(
            MinValueValidator(1, 'Минимальное время приготовления: 1 мин'),
        ),
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientAmount',
        related_name='recipes',
    )
    tags = models.ManyToManyField(Tag, related_name='recipes')

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'рецепты'
        ordering = ('-pub_date',)
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'author'),
                name='%(app_label)s_%(class)s_unique_for_recipe',
            ),
            models.CheckConstraint(
                check=models.Q(name__length__gt=0),
                name='%(app_label)s_%(class)s_name_empty',
            ),
        )

    def __str__(self):
        return self.name


class IngredientAmount(models.Model):
    """Связная модель ORM для рецептов и колличества ингредиентов в них."""

    recipe = models.ForeignKey(
        Recipe,
        verbose_name='рецепты',
        related_name='ingredient_amounts',
        on_delete=models.CASCADE,
    )
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='ингредиенты',
        related_name='ingredient_amounts',
        on_delete=models.CASCADE,
    )
    amount = models.PositiveIntegerField(
        'колличество',
        validators=(MinValueValidator(1, 'Минимум 1 ингредиент'),),
        default=1,
    )

    class Meta:
        verbose_name = 'ингредиенты в рецепте'
        verbose_name_plural = 'ингредиенты в рецептах'
        ordering = ('recipe',)
        constraints = (
            models.UniqueConstraint(
                fields=(
                    'recipe',
                    'ingredient',
                ),
                name='%(app_label)s_%(class)s_unique_for_recipe',
            ),
        )

    def __str__(self) -> str:
        return f'{self.amount} {self.ingredient}'


class Favorite(models.Model):
    """Модель ORM для списка избранных рецептов."""

    user = models.ForeignKey(
        User,
        verbose_name='пользователь',
        on_delete=models.CASCADE,
        related_name='favorite_user',
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='избранное',
        on_delete=models.CASCADE,
        related_name='favorite_recipe',
    )

    class Meta:
        verbose_name = 'избранное'
        verbose_name_plural = 'избранное'
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'user'),
                name='%(app_label)s_%(class)s_unique_favorite',
            ),
        )

    def __str__(self) -> str:
        return f'{self.user}: {self.recipe}'


class ShoppingCart(models.Model):
    """Модель ORM для списка покупок."""

    user = models.ForeignKey(
        User,
        verbose_name='владелец корзины',
        on_delete=models.CASCADE,
        related_name='cart_owner',
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='рецепт в корзине',
        on_delete=models.CASCADE,
        related_name='cart_recipe',
    )

    class Meta:
        verbose_name = 'корзина'
        verbose_name_plural = 'корзины'
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'user'),
                name='%(app_label)s_%(class)s_unique_cart',
            ),
        )

    def __str__(self) -> str:
        return f'{self.user}: {self.recipe}'
