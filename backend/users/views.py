from django.http import HttpRequest
from djoser.conf import settings
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from recipes.serializers import UserSubscribeSerializer
from users.models import Subsription, User


class UsersViewSet(UserViewSet):
    """Кастомный ViewSet для работы с пользователями."""
    def get_permissions(self):
        if self.action in ('subscribe', 'subscriptions'):
            self.permission_classes = settings.PERMISSIONS.user_subscribe
        return super().get_permissions()

    @action(
        detail=False,
        serializer_class=UserSubscribeSerializer,
    )
    def subscriptions(self, request: HttpRequest, *args, **kwargs) -> Response:
        subscribers = User.objects.filter(authors__subscriber=request.user)
        pages = self.paginate_queryset(subscribers)
        serializer = self.get_serializer(pages, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        ['post', 'delete'],
        detail=True,
        serializer_class=UserSubscribeSerializer,
    )
    def subscribe(self, request: HttpRequest, *args, **kwargs) -> Response:
        author = self.get_object()
        subscriber = request.user
        subscription = Subsription.objects.filter(
            author=author, subscriber=subscriber,
        )
        sub_exists = subscription.exists()
        if request.method == 'DELETE':
            if not sub_exists:
                return Response(
                    {'error': 'Вы не подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            subscription.delete()
            return Response(
                {'info': f'Вы отписались от пользователя {author}'},
                status=status.HTTP_204_NO_CONTENT,
            )
        if author == subscriber:
            return Response(
                {'error': 'Нельзя подписаться на себя'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if sub_exists:
            return Response(
                {'error': 'Вы уже подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        Subsription.objects.create(author=author, subscriber=subscriber)
        serializer = self.get_serializer(author)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
