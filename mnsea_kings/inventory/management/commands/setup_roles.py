from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


ROLE_PERMISSIONS = {
    "Inventory Staff": ["inventory.stockmonth", "inventory.stockday", "inventory.stockline", "inventory.stocktransaction"],
    "Sales Staff": ["orders.order", "orders.orderitem", "orders.address"],
    "Accountant": ["inventory.stockmonth", "inventory.stockday", "inventory.stockline", "inventory.stocktransaction", "orders.order", "payments.paymentlog"],
    "Delivery Staff": ["orders.order", "orders.orderitem"],
}


class Command(BaseCommand):
    help = "Create standard staff groups and assign least-privilege permissions."

    def handle(self, *args, **options):
        for group_name, permission_codes in ROLE_PERMISSIONS.items():
            group, _ = Group.objects.get_or_create(name=group_name)
            permissions = []
            for code in permission_codes:
                app_label, model = code.split(".")
                permissions.extend(Permission.objects.filter(content_type__app_label=app_label, content_type__model=model))
            group.permissions.set(permissions)
            self.stdout.write(self.style.SUCCESS(f"{group_name}: {len(permissions)} permissions"))
        self.stdout.write("Add users to groups from Admin > Users. Superusers retain full access.")