from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers

from users.models import User


class UsersSerializer(UserSerializer):
    """Сериализатор для списка пользователей."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'password',
        )
        extra_kwargs = {'password': {'write_only': True}}

    def get_is_subscribed(self, author: User) -> bool:
        subscriber = self.context.get('request').user
        return (
            subscriber.is_authenticated
            and subscriber.subscribers.filter(author=author).exists()
        )


class UserProfileSerializer(UserCreateSerializer):
    """Сериализатор для создания пользователей и получения профиля."""
    class Meta(UserCreateSerializer.Meta):
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )
