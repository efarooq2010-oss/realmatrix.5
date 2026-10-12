"""
Management command to seed 50 players into the first available tournament.
Creates 50 UserProfile accounts and registers them as Teams in the tournament.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from tournament.models import UserProfile, Tournament, Team
import datetime
import random


PLAYER_NAMES = [
    "Alex Storm", "Blaze King", "Cyber Wolf", "Dark Rider", "Echo Force",
    "Falcon Eye", "Ghost Shot", "Hunter X", "Iron Fist", "Jade Viper",
    "Kilo Blaze", "Luna Fire", "Maximus", "Nova Strike", "Omega One",
    "Phantom X", "Quantum Ray", "Reaper Zero", "Shadow Man", "Titan Rush",
    "Ultra Blade", "Venom Snake", "Wrath Khan", "Xeon Speed", "Yeti Force",
    "Zeus Bolt", "Alpha Wolf", "Beta Surge", "Crimson Arc", "Delta Fire",
    "Ember Claw", "Frost Bite", "Ghost Pulse", "Havoc King", "Inferno X",
    "Jinx Blade", "Kairo Shot", "Laser Edge", "Mystic Eye", "Neon Rage",
    "Obsidian", "Phantom Storm", "Quickfire", "Rampage X", "Stealth Pro",
    "Thunder Clan", "Uprising", "Vortex King", "Wildfire X", "Zombie Rush",
]


class Command(BaseCommand):
    help = 'Seed 50 players into the first available tournament'

    def handle(self, *args, **options):
        # Get or create a tournament to seed players into
        tournament = Tournament.objects.first()
        if not tournament:
            self.stdout.write(self.style.ERROR("No tournaments found. Please create a tournament first."))
            return

        self.stdout.write(f"Seeding 50 players into tournament: {tournament.name}")

        created_count = 0
        skipped_count = 0

        for i, name in enumerate(PLAYER_NAMES, start=1):
            game_id = f"FF{i:04d}{random.randint(100, 999)}"
            gmail = f"player{i}.{name.replace(' ', '').lower()}@ffarena.com"
            username = gmail

            # Create player user if doesn't exist
            if UserProfile.objects.filter(gmail=gmail).exists():
                user = UserProfile.objects.get(gmail=gmail)
                skipped_count += 1
            else:
                user = UserProfile(
                    full_name=name,
                    game_id=game_id,
                    gmail=gmail,
                    username=username,
                    email=gmail,
                    phone_number=f"+39{random.randint(3000000000, 3999999999)}",
                )
                user.set_password("Player@1234")
                user.save()
                created_count += 1

            # Register as a team/player in the tournament
            team_name = f"{name}'s Squad"
            if not Team.objects.filter(tournament=tournament, team_name=team_name).exists():
                Team.objects.create(
                    tournament=tournament,
                    team_name=team_name,
                    captain=user,
                    players=[{"role": "Captain", "name": name, "free_fire_id": user.game_id}],
                    payment_status="Paid",
                )

        # Update tournament slots_available
        total_joined = Team.objects.filter(tournament=tournament).count()
        tournament.slots_available = max(0, tournament.slots_total - total_joined)
        tournament.save()

        self.stdout.write(self.style.SUCCESS(
            f"Done! Created {created_count} new players, skipped {skipped_count} existing.\n"
            f"Total teams in tournament '{tournament.name}': {total_joined}\n"
            f"Slots available: {tournament.slots_available}/{tournament.slots_total}"
        ))
