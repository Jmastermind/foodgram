from django.conf import settings
from django.db.models import Model, Sum
from django.http import HttpRequest, HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from fpdf import FPDF
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS
from rest_framework.response import Response

from foodgram_backend.permissions import AuthorStuffReadOnly
from recipes.filters import RecipeFilter
from recipes.models import (
    Favorite,
    Ingredient,
    IngredientAmount,
    Recipe,
    ShoppingCart,
    Tag,
)
from recipes.serializers import (
    IngredientSerializer,
    RecipeSerializerModify,
    RecipeSerializerRetrieve,
    ShortRecipeSerializer,
    TagSerializer,
)
from users.models import User


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с ингредиентами блюда."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None

    def get_queryset(self) -> list[Ingredient]:
        name: str = self.request.query_params.get('name')
        if not name:
            return self.queryset
        start_queryset = self.queryset.filter(name__istartswith=name)
        start_names = start_queryset.values_list('name')
        contain_queryset = self.queryset.filter(name__icontains=name).exclude(
            name__in=start_names,
        )
        return list(start_queryset) + list(contain_queryset)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с рецептами."""
    queryset = Recipe.objects.all()
    permission_classes = (AuthorStuffReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeSerializerRetrieve
        return RecipeSerializerModify

    def manage_relation(self, model: Model, user: User, mode: str) -> Response:
        recipe = self.get_object()
        obj = model.objects.filter(user=user, recipe=recipe)
        existed = obj.exists()
        if mode == 'del':
            if not existed:
                return Response(
                    {
                        'error': f'Рецепт {recipe} отсутствует в списке',
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            obj.delete()
            return Response(
                {'info': f'Рецепт {recipe} был исключен из списка'},
                status=status.HTTP_204_NO_CONTENT,
            )
        if existed:
            return Response(
                {'error': f'Рецепт {recipe} уже добавлен'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        model.objects.create(user=user, recipe=recipe)
        serializer = self.get_serializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        ('post', 'delete'),
        detail=True,
        serializer_class=ShortRecipeSerializer,
        permission_classes=(permissions.IsAuthenticated,),
    )
    def favorite(self, request: HttpRequest, **kwargs) -> Response:
        if request.method == 'DELETE':
            return self.manage_relation(Favorite, request.user, 'del')
        return self.manage_relation(Favorite, request.user, 'add')

    @action(
        ('post', 'delete'),
        detail=True,
        serializer_class=ShortRecipeSerializer,
        permission_classes=(permissions.IsAuthenticated,),
    )
    def shopping_cart(self, request: HttpRequest, **kwargs) -> Response:
        if request.method == 'DELETE':
            return self.manage_relation(ShoppingCart, request.user, 'del')
        return self.manage_relation(ShoppingCart, request.user, 'add')

    @action(detail=False)
    def download_shopping_cart(self, request: HttpRequest) -> Response:
        """Составление и скачивание списка покупок."""
        user = request.user
        ingredients = (
            IngredientAmount.objects.filter(recipe__cart_recipe__user=user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(Sum('amount', distinct=True))
        )
        pdf = FPDF()
        pdf.add_page()
        font_regular = (
            settings.DATA_DIR / 'font' / 'NotoSans-Regular.ttf'
        ).resolve()
        font_bold = (
            settings.DATA_DIR / 'font' / 'NotoSans-Bold.ttf'
        ).resolve()
        pdf.add_font('Sans', style='', fname=font_regular, uni=True)
        pdf.add_font('Sans', style='B', fname=font_bold, uni=True)
        pdf.set_font('Sans', 'B', size=14)
        pdf.cell(txt='Список покупок', center=True)
        pdf.ln(8)
        pdf.set_font('Sans', '', size=14)
        for i, ingredient in enumerate(ingredients):
            pdf.cell(
                40,
                10,
                f'{i + 1}) {ingredient["ingredient__name"]}'
                f' - {ingredient["amount__sum"]} '
                f'{ingredient["ingredient__measurement_unit"]}',
            )
            pdf.ln()
        response = HttpResponse(
            content_type='application/pdf; charset=utf-8',
            status=status.HTTP_200_OK,
        )
        response[
            'Content-Disposition'
        ] = 'attachment; filename="shopping_cart.pdf"'
        response.write(bytes(pdf.output(dest='S')))
        return response
