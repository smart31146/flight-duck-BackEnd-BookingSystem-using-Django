from django.core.management.base import BaseCommand
from users.models import NewUser

class Command(BaseCommand):

    def handle(self, *args, **options):
        NewUser.objects.create_superuser("gurjasadmin@yopmail.com", "gurjasadmin")