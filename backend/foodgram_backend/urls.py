from django.apps import apps
from django.contrib import admin
from django.urls import include, path

urlpatterns = (
    path('admin/', admin.site.urls),
    path(
        'api/',
        include('users.urls', namespace=apps.get_app_config('users').name),
    ),
    path(
        'api/',
        include('recipes.urls', namespace=apps.get_app_config('recipes').name),
    ),
)
