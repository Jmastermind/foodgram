from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    username = models.CharField(
        max_length=150,
        unique=True,
    )
    first_name = models.CharField(
        'имя',
        max_length=150,
    )
    last_name = models.CharField(
        'фамилия',
        max_length=150,
    )
    email = models.EmailField(
        unique=True,
    )

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'пользователи'
        ordering = ('id',)


class Subsription(models.Model):
    subscriber = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='подписчик',
        related_name='subscribers',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='автор',
        related_name='authors',
    )

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'подписки'
        constraints = (
            models.UniqueConstraint(
                fields=('subscriber', 'author'),
                name='%(app_label)s_%(class)s_name_unique',
            ),
            models.CheckConstraint(
                check=~models.Q(author=models.F('subscriber')),
                name='%(app_label)s_%(class)s_self_sub',
            ),
        )

    def __str__(self) -> str:
        return f'{self.subscriber} -> {self.author}'
