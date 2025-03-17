import csv

from django.core.management.base import BaseCommand

from recipes.models import Ingredient

PATH_TO_CSV = 'static/ingredients.csv'


class Command(BaseCommand):
    help = 'Imports data from a CSV file into the YourModel model'

    def import_data(self):
        with open(PATH_TO_CSV, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                Ingredient.objects.create(
                    name=row['name'],
                    measurement_unit=row['measurement_unit'],
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Ингредиент {row["name"]} успешно добавлен '
                    )
                )

    def handle(self, *args, **options):
        self.import_data()
        self.stdout.write(self.style.SUCCESS('Data imported successfully'))
