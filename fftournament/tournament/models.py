from decimal import Decimal
from django.contrib.auth.models import AbstractUser
from django.db import models

class UserProfile(AbstractUser):
    MEMBERSHIP_CHOICES = [
        ('', 'None'),
        ('Silver', 'Silver'),
        ('Gold', 'Gold'),
        ('Diamond', 'Diamond'),
    ]
    full_name = models.CharField(max_length=150)
    game_id = models.CharField(max_length=50, unique=True)
    gmail = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15)
    membership_tier = models.CharField(max_length=20, choices=MEMBERSHIP_CHOICES, default='', blank=True)
    membership_upgraded_at = models.DateTimeField(null=True, blank=True)
    diamonds = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('100.00'))  # Diamond Currency (1 Euro = 1 Diamond)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def active_membership_tier(self):
        if not self.membership_tier:
            return ''
        if not self.membership_upgraded_at:
            return ''
        from django.utils import timezone
        from datetime import timedelta
        if timezone.now() < self.membership_upgraded_at + timedelta(days=30):
            return self.membership_tier
        return ''

    def save(self, *args, **kwargs):
        # Auto-populate username and email fields from gmail for compatibility with Django's internal auth
        if self.gmail:
            self.email = self.gmail
            if not self.username:
                self.username = self.gmail
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} ({self.game_id}) - 💎{self.diamonds}"


class WalletTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('TOPUP', 'Diamond Top Up (+💎)'),
        ('CASHOUT', 'Real Money Cash Out (-💎)'),
        ('ENTRY_FEE', 'Tournament Entry Fee (-💎)'),
        ('SUBSCRIPTION', 'Manager Subscription (-💎)'),
        ('PRIZE_WIN', 'Tournament Winnings (+💎)'),
    ]
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='wallet_transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount_diamonds = models.DecimalField(max_digits=12, decimal_places=2)  # Diamonds (+ or -)
    amount_euros = models.DecimalField(max_digits=12, decimal_places=2)     # Equivalent Euros (1:1)
    description = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='Completed')

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.full_name} - {self.transaction_type}: 💎{self.amount_diamonds} ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"



class Tournament(models.Model):
    MODE_CHOICES = [
        ('Solo', 'Solo'),
        ('Duo', 'Duo'),
        ('Squad', 'Squad'),
        ('1v1', '1v1'),
        ('2v2', '2v2'),
    ]
    STATUS_CHOICES = [
        ('Upcoming', 'Upcoming'),
        ('Ongoing', 'Ongoing'),
        ('Completed', 'Completed'),
    ]
    name = models.CharField(max_length=200)
    mode = models.CharField(max_length=10, choices=MODE_CHOICES)
    date = models.DateTimeField()
    entry_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    prize_pool = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    slots_total = models.IntegerField(default=48)
    slots_available = models.IntegerField(default=48)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='Upcoming')
    creator = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='hosted_tournaments')
    custom_room_id = models.CharField(max_length=50, blank=True, default='')
    custom_room_password = models.CharField(max_length=50, blank=True, default='')

    def save(self, *args, **kwargs):
        import random
        if not self.custom_room_id:
            self.custom_room_id = f"ROOM-{random.randint(100000, 999999)}"
        if not self.custom_room_password:
            self.custom_room_password = f"FF-{random.randint(1000, 9999)}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.mode})"



class Team(models.Model):
    PAYMENT_CHOICES = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
    ]
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='teams')
    team_name = models.CharField(max_length=100)
    captain = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='captained_teams')
    # players contains list of players: [{"name": "...", "game_id": "..."}, ...]
    players = models.JSONField(default=list)
    payment_status = models.CharField(max_length=15, choices=PAYMENT_CHOICES, default='Pending')

    def __str__(self):
        return f"{self.team_name} (Capt: {self.captain.full_name})"


class Match(models.Model):
    STATUS_CHOICES = [
        ('Upcoming', 'Upcoming'),
        ('Live', 'Live'),
        ('Completed', 'Completed'),
    ]
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='matches')
    team1 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='matches_as_team1', null=True, blank=True)
    team2 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='matches_as_team2', null=True, blank=True)
    match_time = models.DateTimeField()
    winner = models.ForeignKey(Team, on_delete=models.SET_NULL, related_name='matches_won', null=True, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='Upcoming')
    map_name = models.CharField(max_length=50, default='Bermuda')

    def __str__(self):
        t1 = self.team1.team_name if self.team1 else "TBD"
        t2 = self.team2.team_name if self.team2 else "TBD"
        return f"{t1} vs {t2} - {self.tournament.name} ({self.status})"


class Score(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='scores')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='scores')
    kills = models.IntegerField(default=0)
    placement = models.IntegerField(default=0)
    points = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.team.team_name} in Match {self.match.id} ({self.points} pts)"


class PaymentRecord(models.Model):
    TIER_CHOICES = [
        ('Silver', 'Silver'),
        ('Gold', 'Gold'),
        ('Diamond', 'Diamond'),
    ]
    TIER_PRICES = {
        'Silver': 9.99,
        'Gold': 24.99,
        'Diamond': 49.99,
    }
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='payments')
    tier = models.CharField(max_length=20, choices=TIER_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    cardholder_name = models.CharField(max_length=150)
    card_number = models.CharField(max_length=19)  # Stored masked: **** **** **** 1234
    card_expiry = models.CharField(max_length=5)    # MM/YY
    cvv = models.CharField(max_length=4)            # Stored masked: ***
    payment_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='Completed')

    def __str__(self):
        return f"{self.user.full_name} - {self.tier} (€{self.amount}) on {self.payment_date.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        ordering = ['-payment_date']


class PlatformNews(models.Model):
    CATEGORY_CHOICES = [
        ('Update', 'System Update'),
        ('Event', 'Tournament Event'),
        ('Maintenance', 'Maintenance'),
        ('Announcement', 'General Announcement'),
    ]
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='Update')
    content = models.TextField()
    badge = models.CharField(max_length=30, default='NEW', blank=True)
    author = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='published_news')
    created_at = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.category}] {self.title}"

