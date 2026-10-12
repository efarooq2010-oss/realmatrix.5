"""
Django Management Command to initialize Diamond balances and wallet transactions in db.sqlite3.
"""
from django.core.management.base import BaseCommand
from tournament.models import UserProfile, WalletTransaction
from decimal import Decimal

class Command(BaseCommand):
    help = 'Initialize Diamond Currency balance for all UserProfiles in SQLite DB'

    def handle(self, *args, **options):
        users = UserProfile.objects.all()
        updated_count = 0
        
        for user in users:
            if user.diamonds is None or user.diamonds == 0:
                user.diamonds = Decimal('100.00')
                user.save()
                updated_count += 1
                
                # Create initial welcome bonus wallet transaction
                WalletTransaction.objects.get_or_create(
                    user=user,
                    transaction_type='TOPUP',
                    amount_diamonds=Decimal('100.00'),
                    amount_euros=Decimal('100.00'),
                    description='Welcome Bonus 💎100 Diamonds Credited',
                    defaults={'status': 'Completed'}
                )
                
        self.stdout.write(self.style.SUCCESS(
            f"Successfully checked {users.count()} users in SQLite DB!\n"
            f" - Updated {updated_count} user accounts with 💎100.00 starting balance.\n"
            f" - All database accounts now have active 💎 Diamond balances in DB Browser (SQLite)!"
        ))
