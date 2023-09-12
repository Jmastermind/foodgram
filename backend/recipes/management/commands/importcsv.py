import csv

from decouple import config
from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient, Tag, User

ADMIN_PASSWORD = config('ADMIN_PASSWORD', default='admin')


class Command(BaseCommand):
    """
    Imports tables from CSV files.

    Sometimes you will need to clear your db before using this command.

    Использование:
    ```
    manage.py flush
    manage.py importcsv [-s, --silent]
    ```
    """

    help = 'Imports tables from CSV files'

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            '-s',
            '--silent',
            action='store_true',
            help='Hide creation messages.',
        )

    def handle(self, *args, **options) -> None:
        del args
        data = (
            ('ingredients.csv', Ingredient, 'Ингредиенты'),
            ('tags.csv', Tag, 'Tag'),
            ('users.csv', User, 'User'),
        )
        for item in data:
            with open(
                settings.DATA_DIR / item[0],
                encoding='utf-8',
            ) as f:
                dreaded = csv.DictReader(f)
                for row in dreaded:
                    obj, created = item[1].objects.update_or_create(**row)  # type: ignore # noqa: E501
                    if created and not options['silent']:
                        print(f'{item[2]} `{obj}` has been created.')
                    if isinstance(obj, User):
                        password = (
                            obj.username if obj.username != 'adam'
                            else ADMIN_PASSWORD
                        )
                        obj.set_password(password)
                        obj.save()
