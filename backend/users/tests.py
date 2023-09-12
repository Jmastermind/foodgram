from django.urls import reverse
from mixer.backend.django import mixer
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from users.models import Subsription, User


class UsersTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_user_registration(self) -> None:
        url = reverse('users:user-list')
        data = {
            'email': 'user_1@fake.com',
            'username': 'user_1',
            'first_name': 'User1',
            'last_name': 'User1',
            'password': 'fake_pswd_1',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            response.json(),
        )
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get(pk=1).username, data['username'])

    def test_user_registration_missing_field(self) -> None:
        url = reverse('users:user-list')
        data = {
            'email': 'user_1@fake.com',
            'username': 'user_1',
            'first_name': 'User1',
            'password': 'fake_pswd_1',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            response.json(),
        )
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(
            response.json()['last_name'][0],
            'Обязательное поле.',
        )

    def test_user_list_fields(self) -> None:
        user = mixer.blend(User)
        url = reverse('users:user-list')
        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.json(),
        )
        self.assertEqual(
            response.json()['results'][0]['last_name'],
            user.last_name,
        )

    def test_user_list_pagination_limit(self) -> None:
        mixer.cycle(4).blend(User)
        url = reverse('users:user-list')
        response = self.client.get(url, {'limit': '2'})
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.json(),
        )
        self.assertEqual(
            len(response.json()['results']),
            2,
        )

    def test_me(self) -> None:
        user = mixer.blend(User)
        url = reverse('users:user-me')
        self.client.force_authenticate(user)
        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.json(),
        )
        self.assertEqual(
            response.json()['last_name'],
            user.last_name,
        )

    def test_user_profile(self) -> None:
        user = mixer.blend(User)
        url = reverse('users:user-detail', args=(user.pk,))
        self.client.force_authenticate(user)
        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.json(),
        )
        self.assertFalse(response.json()['is_subscribed'])

    def test_user_profile_anonymous(self) -> None:
        user = mixer.blend(User)
        url = reverse('users:user-detail', args=(user.pk,))
        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            response.json(),
        )

    def test_user_password_set(self) -> None:
        user = User.objects.create_user(
            username='user', email='email@example.com', password='pass',
        )
        self.client.force_authenticate(user)
        data = {'new_password': 'fake_pswd_1', 'current_password': 'pass'}
        url = reverse('users:user-set-password')
        response = self.client.post(url, data, format='json')
        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

    # Tokens

    def test_token_obtain_email_as_login(self) -> None:
        user = User.objects.create_user(
            username='user', email='email@example.com', password='pass',
        )
        url = reverse('users:login')
        data = {
            'email': user.email,
            'password': 'pass',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.json(),
        )
        self.assertEqual(Token.objects.count(), 1)

    def test_token_destroy(self) -> None:
        user = User.objects.create_user(
            username='user', email='email@example.com', password='pass',
        )
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        url = reverse('users:logout')
        response = self.client.post(url, format='json')
        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )


class SubscriptionTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_subscribtions(self) -> None:
        author_1 = mixer.blend(User)
        author_2 = mixer.blend(User)
        subscriber = mixer.blend(User)
        self.client.force_authenticate(subscriber)
        Subsription.objects.create(author=author_1, subscriber=subscriber)
        Subsription.objects.create(author=author_2, subscriber=subscriber)
        url = reverse('users:user-subscriptions')
        response = self.client.get(url, {'limit': '1'})
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.json(),
        )
        self.assertEqual(
            len(response.json()['results']),
            1,
        )

    def test_subscribe(self) -> None:
        author = mixer.blend(User)
        subscriber = mixer.blend(User)
        self.client.force_authenticate(subscriber)
        url = reverse('users:user-subscribe', args=(author.pk,))
        response = self.client.post(url, format='json')
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            response.json(),
        )
        self.assertTrue(
            Subsription.objects.filter(
                author=author, subscriber=subscriber,
            ).exists(),
        )

    def test_unsubscribe(self) -> None:
        author = mixer.blend(User)
        subscriber = mixer.blend(User)
        self.client.force_authenticate(subscriber)
        Subsription.objects.create(author=author, subscriber=subscriber)
        url = reverse('users:user-subscribe', args=(author.pk,))
        response = self.client.delete(url, format='json')
        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )
        self.assertEqual(Subsription.objects.count(), 0)
