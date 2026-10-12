"""
Django Management Command to Seed 50 Players into a Tournament.
Saves 50 UserProfiles, 50 Teams (Paid), and 50 PaymentRecords directly into db.sqlite3.
"""
import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from tournament.models import UserProfile, Tournament, Team, PaymentRecord

PLAYER_NAMES = [
    "Alex Mercer", "Marcus Vance", "Elena Rostova", "Dante Cross", "Sora Takahashi",
    "Viktor Reznov", "Aria Stark", "Klaus Mikaelson", "Sarah Connor", "Leon Kennedy",
    "Ada Wong", "Jill Valentine", "Chris Redfield", "Claire Redfield", "Nathan Drake",
    "Lara Croft", "Geralt Rivia", "Yennefer Vengerberg", "Triss Merigold", "Ciri Cirilla",
    "Arthur Morgan", "John Marston", "Dutch VanDerLinde", "Sadie Adler", "Charles Smith",
    "Jin Sakai", "Kazuma Kiryu", "Goro Majima", "Ichiban Kasuga", "Cloud Strife",
    "Tifa Lockhart", "Sephiroth Crescent", "Squall Leonhart", "Rinoa Heartilly", "Zack Fair",
    "Noctis Lucis", "Ignis Scientia", "Gladiolus Amicitia", "Prompto Argentum", "Lightning Farron",
    "Balthier MacBun", "Fran Viera", "Vaan Rabanastre", "Penelo Rabanastre", "Ashe Balthier",
    "Snow Villiers", "Sazh Katzroy", "Vanille Oerba", "Fang Oerba", "Hope Estheim"
]

class Command(BaseCommand):
    help = 'Seed 50 players and teams into a tournament in db.sqlite3'

    def handle(self, *args, **options):
        # 1. Get or create target tournament with custom room credentials
        tournament = Tournament.objects.first()
        if not tournament:
            tournament = Tournament.objects.create(
                name="Free Fire Championship Season 1",
                mode="Solo",
                date=timezone.now() + timezone.timedelta(days=2),
                entry_fee=5.00,
                prize_pool=200.00,
                slots_total=60,
                slots_available=60,
                status="Upcoming",
                custom_room_id="ROOM-883920",
                custom_room_password="FF-9941"
            )
        else:
            if not tournament.custom_room_id:
                tournament.custom_room_id = f"ROOM-{random.randint(100000, 999999)}"
            if not tournament.custom_room_password:
                tournament.custom_room_password = f"FF-{random.randint(1000, 9999)}"
            tournament.slots_total = max(tournament.slots_total, 60)
            tournament.save()

        self.stdout.write(f"Target Tournament: '{tournament.name}' (Room ID: {tournament.custom_room_id}, Pass: {tournament.custom_room_password})")

        created_users = 0
        created_teams = 0
        created_payments = 0

        for i, name in enumerate(PLAYER_NAMES, start=1):
            gmail = f"player_{i:02d}_{name.lower().replace(' ', '')}@ffarena.com"
            game_id = f"FF{88000 + i}"
            phone = f"+39340998{i:04d}"

            # Create UserProfile if not exists
            user, u_created = UserProfile.objects.get_or_create(
                gmail=gmail,
                defaults={
                    'full_name': name,
                    'game_id': game_id,
                    'username': gmail,
                    'email': gmail,
                    'phone_number': phone,
                }
            )
            if u_created:
                user.set_password("PlayerPass123!")
                user.save()
                created_users += 1

            team_name = f"{name}'s Squad"

            # Create Team if not exists
            team, t_created = Team.objects.get_or_create(
                tournament=tournament,
                captain=user,
                defaults={
                    'team_name': team_name,
                    'players': [
                        {'role': 'Main Player 1', 'name': name, 'free_fire_id': game_id},
                        {'role': 'Main Player 2', 'name': f"{name} Ally 1", 'free_fire_id': f"{game_id}_1"},
                        {'role': 'Main Player 3', 'name': f"{name} Ally 2", 'free_fire_id': f"{game_id}_2"},
                        {'role': 'Main Player 4', 'name': f"{name} Ally 3", 'free_fire_id': f"{game_id}_3"},
                    ],
                    'payment_status': 'Paid'
                }
            )
            if t_created:
                created_teams += 1

            # Create PaymentRecord for Entry Fee
            card_last4 = f"{1000 + i:04d}"
            pmt, p_created = PaymentRecord.objects.get_or_create(
                user=user,
                amount=tournament.entry_fee,
                cardholder_name=name,
                defaults={
                    'tier': 'Entry Fee',
                    'card_number': f'**** **** **** {card_last4}',
                    'card_expiry': '12/28',
                    'cvv': '***',
                    'status': 'Completed'
                }
            )
            if p_created:
                created_payments += 1

        # Update tournament available slots
        total_registered_teams = Team.objects.filter(tournament=tournament).count()
        tournament.slots_available = max(0, tournament.slots_total - total_registered_teams)
        tournament.save()

        self.stdout.write(self.style.SUCCESS(
            f"Successfully populated database tables!\n"
            f" - Users created: {created_users}\n"
            f" - Teams joined: {created_teams} (Total in tournament: {total_registered_teams})\n"
            f" - Payment records saved: {created_payments}\n"
            f" - Tournament Available Slots: {tournament.slots_available} / {tournament.slots_total}\n"
            f" - Custom Room ID: {tournament.custom_room_id}\n"
            f" - Custom Room Pass: {tournament.custom_room_password}\n"
            f"All records are saved in DB Browser (SQLite) database!"
        ))
