from django.urls import include, path
from rest_framework.routers import DefaultRouter

from users.views import UsersViewSet

app_name = '%(app_label)s'

router = DefaultRouter()
router.register('users', UsersViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
