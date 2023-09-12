from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import SafeString, mark_safe

from recipes.models import (
    Favorite,
    Ingredient,
    IngredientAmount,
    Recipe,
    ShoppingCart,
    Tag,
)
from users.models import Subsription, User


class BaseAdmin(admin.ModelAdmin):
    empty_value_display = '-empty-'


@admin.register(User)
class UserAdmin(BaseAdmin):
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'is_staff',
        'get_subscribers',
    )
    list_filter = ('username', 'email')

    @admin.display(description='подписчиков')
    def get_subscribers(self, user: User) -> int:
        return user.authors.count()


@admin.register(Subsription)
class SubsriptionAdmin(BaseAdmin):
    list_display = ('__str__', 'author', 'subscriber')
    list_filter = ('author', 'subscriber')


@admin.register(Ingredient)
class IngredientAdmin(BaseAdmin):
    list_display = (
        'name',
        'measurement_unit',
    )
    list_filter = ('name',)
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(BaseAdmin):
    list_display = (
        'name',
        'color_code',
        'slug',
    )
    search_fields = ('name', 'color')

    @admin.display(description='цвет')
    def color_code(self, obj: Tag) -> SafeString:
        return format_html(
            f'<span style="color:{obj.color};">{obj.color}</span>',
        )


@admin.register(Favorite)
class FavoriteAdmin(BaseAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@admin.register(ShoppingCart)
class CardAdmin(BaseAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@admin.register(IngredientAmount)
class IngredientAmountAdmin(BaseAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')


class IngredientInline(admin.TabularInline):
    model = IngredientAmount
    extra = 0


@admin.register(Recipe)
class RecipeAdmin(BaseAdmin):
    list_display = (
        'name',
        'author',
        'get_image',
        'get_ingredients',
        'get_tags',
        'get_favorites',
    )
    fields = (
        (
            'name',
            'cooking_time',
        ),
        (
            'author',
            'tags',
        ),
        ('text',),
        ('image',),
    )
    raw_id_fields = ('author',)
    search_fields = (
        'name',
        'author__username',
        'tags__name',
    )
    list_filter = ('name', 'author__username', 'tags__name')

    inlines = (IngredientInline,)

    @admin.display(description='изображение')
    def get_image(self, obj: Recipe) -> SafeString:
        return mark_safe(f'<img src={obj.image.url} width="160" hieght="90"')

    @admin.display(description='ингредиенты')
    def get_ingredients(self, obj: Recipe) -> int:
        return obj.ingredients.count()

    @admin.display(description='теги')
    def get_tags(self, obj: Recipe) -> int:
        return obj.tags.count()

    @admin.display(description='в избранном')
    def get_favorites(self, obj: Recipe) -> int:
        return obj.favorite_recipe.count()
