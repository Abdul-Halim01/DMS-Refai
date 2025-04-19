from django.core.management.base import BaseCommand
from users.models import Criteria

# Define your fixed set of criteria here
CRITERIA_MAP = [
    {"name": "HR", "criteria_type": "add"},
    {"name": "HR", "criteria_type": "edit"},
    {"name": "HR", "criteria_type": "delete"},
    {"name": "Form", "criteria_type": "add"},
    {"name": "Form", "criteria_type": "edit"},
    {"name": "Form", "criteria_type": "delete"},
    {"name": "Tasks", "criteria_type": "add"},
    {"name": "Tasks", "criteria_type": "edit"},
    {"name": "Tasks", "criteria_type": "delete"},
    {"name": "Data", "criteria_type": "edit"},
    {"name": "Data", "criteria_type": "delete"},
    {"name": "Data", "criteria_type": "add"},
    {"name": "Users", "criteria_type": "add"},
    {"name": "Users", "criteria_type": "edit"},
    {"name": "Users", "criteria_type": "delete"},
    {"name": "Documents", "criteria_type": "add"},
    {"name": "Documents", "criteria_type": "edit"},
    {"name": "Documents", "criteria_type": "delete"},
    # Add more as needed
]

class Command(BaseCommand):
    help = 'Create a fixed set of Criteria objects as defined in the CRITERIA_MAP.'

    def handle(self, *args, **options):
        for item in CRITERIA_MAP:
            name = item["name"]
            criteria_type = item["criteria_type"]
            if Criteria.objects.filter(name=name, criteria_type=criteria_type).exists():
                self.stdout.write(self.style.WARNING(f'Criteria with name "{name}" and type "{criteria_type}" already exists.'))
                continue
            criteria = Criteria.objects.create(name=name, criteria_type=criteria_type)
            self.stdout.write(self.style.SUCCESS(f'Successfully created criteria: {criteria}'))
