from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, Http404
import os
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.utils import timezone
from django import forms
from .models import Tournament, Team, Match, Score, UserProfile, PlatformNews, WalletTransaction, PaymentRecord

# User Registration Form
class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control bg-dark-blue text-light border-neon-cyan',
        'placeholder': 'Min 6 characters',
        'minlength': '6',
        'id': 'reg-password'
    }))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control bg-dark-blue text-light border-neon-cyan',
        'placeholder': 'Confirm Password',
        'id': 'reg-confirm-password'
    }))

    class Meta:
        model = UserProfile
        fields = ['full_name', 'game_id', 'gmail', 'phone_number', 'password']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control bg-dark-blue text-light border-neon-cyan',
                'placeholder': 'Enter Full Name',
                'id': 'reg-fullname'
            }),
            'game_id': forms.TextInput(attrs={
                'class': 'form-control bg-dark-blue text-light border-neon-cyan',
                'placeholder': '1234567890',
                'id': 'reg-gameid'
            }),
            'gmail': forms.EmailInput(attrs={
                'class': 'form-control bg-dark-blue text-light border-neon-cyan',
                'placeholder': 'example@gmail.com',
                'id': 'reg-gmail'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control bg-dark-blue text-light border-neon-cyan',
                'placeholder': '+1234567890',
                'pattern': r'^[+]*[(]{0,1}[0-9]{1,4}[)]{0,1}[-\s\./0-9]*$',
                'id': 'reg-phone'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data


def home(request):
    featured_tournament = Tournament.objects.filter(status='Upcoming').first()
    if not featured_tournament:
        featured_tournament = Tournament.objects.first()
    
    # Next upcoming tournament for countdown
    next_tournament = Tournament.objects.filter(status='Upcoming').order_by('date').first()
    if not next_tournament:
        next_tournament = Tournament.objects.all().order_by('date').first()
    
    # Recent winners: teams that placed 1st in completed match scores
    recent_winners_scores = Score.objects.filter(placement=1, match__status='Completed').order_by('-match__match_time')[:3]
    recent_winners = []
    for s in recent_winners_scores:
        recent_winners.append({
            'team_name': s.team.team_name,
            'captain': s.team.captain.full_name,
            'tournament': s.match.tournament.name,
            'kills': s.kills,
            'points': s.points
        })
        
    # If no winners in database, supply mock default winners to show on landing page
    if not recent_winners:
        recent_winners = [
            {'team_name': 'Team Vipers', 'captain': 'Alex Mercer', 'tournament': 'Free Fire Season 5', 'kills': 14, 'points': 26},
            {'team_name': 'Inferno Lords', 'captain': 'Klaus Mikaelson', 'tournament': 'Squad Clash Pro', 'kills': 18, 'points': 30},
            {'team_name': 'Alpha Squad', 'captain': 'Sarah Connor', 'tournament': 'Cyber Solo Cup', 'kills': 10, 'points': 22},
        ]
        
    context = {
        'featured_tournament': featured_tournament,
        'next_tournament': next_tournament,
        'recent_winners': recent_winners,
    }
    return render(request, 'tournament/home.html', context)


def tournaments_list(request):
    tournaments = Tournament.objects.all().order_by('date')
    context = {
        'tournaments': tournaments,
    }
    return render(request, 'tournament/tournaments.html', context)


def register_user(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, "Registration successful! Cyber account created.")
            return redirect('login')
        else:
            messages.error(request, "Registration failed. Please check form details.")
    else:
        form = UserRegistrationForm()
    return render(request, 'tournament/register.html', {'form': form})


def login_user(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username_or_email = (request.POST.get('username') or '').strip()
        password = request.POST.get('password') or ''
        remember_me = request.POST.get('remember_me')
        
        try:
            user = authenticate(request, username=username_or_email, password=password)
        except Exception:
            user = None

        if user is not None:
            login(request, user)
            if not remember_me:
                request.session.set_expiry(0)  # Expires when browser closes
            messages.success(request, f"Welcome back, Captain {user.full_name}!")
            # Admin auto‑redirect after login
            if user.email == 'admin@gmail.com' or user.is_staff:
                return redirect('admin_dashboard')
            return redirect('home')
        else:
            messages.error(request, "Invalid Gmail/Username or Password.")
    return render(request, 'tournament/login.html')


def logout_user(request):
    logout(request)
    messages.success(request, "Logged out successfully. See you in the arena!")
    return redirect('home')

def admin_dashboard(request):
    # Only staff/admin can access
    if not request.user.is_staff:
        return redirect('home')

    # Key Metrics
    total_users = UserProfile.objects.count()
    new_today = UserProfile.objects.filter(created_at__date=timezone.now().date()).count()
    manager_counts = {
        'Silver': UserProfile.objects.filter(membership_tier='Silver').count(),
        'Gold': UserProfile.objects.filter(membership_tier='Gold').count(),
        'Diamond': UserProfile.objects.filter(membership_tier='Diamond').count(),
    }
    total_managers = manager_counts['Silver'] + manager_counts['Gold'] + manager_counts['Diamond']
    
    total_tournaments = Tournament.objects.count()
    tournament_status = {
        'Upcoming': Tournament.objects.filter(status='Upcoming').count(),
        'Ongoing': Tournament.objects.filter(status='Ongoing').count(),
        'Completed': Tournament.objects.filter(status='Completed').count(),
    }
    total_matches = Match.objects.count()
    total_teams = Team.objects.count()

    total_diamonds = UserProfile.objects.aggregate(total=Sum('diamonds'))['total'] or 0
    total_topup = WalletTransaction.objects.filter(transaction_type='TOPUP').aggregate(total=Sum('amount_euros'))['total'] or 0
    total_cashout = WalletTransaction.objects.filter(transaction_type='CASHOUT', status='Completed').aggregate(total=Sum('amount_euros'))['total'] or 0
    total_subscriptions = PaymentRecord.objects.filter(status='Completed').aggregate(total=Sum('amount'))['total'] or 0
    net_revenue = (total_topup or 0) + (total_subscriptions or 0) - (total_cashout or 0)

    # Activity Feed
    recent_users = UserProfile.objects.order_by('-created_at')[:6]
    recent_tournaments = Tournament.objects.order_by('-date')[:6]
    recent_topups = WalletTransaction.objects.filter(transaction_type='TOPUP').order_by('-timestamp')[:6]
    recent_cashouts_tx = WalletTransaction.objects.filter(transaction_type='CASHOUT').order_by('-timestamp')[:6]
    recent_news = PlatformNews.objects.order_by('-created_at')[:6]

    activity = []
    for u in recent_users:
        activity.append({'time': u.created_at, 'type': 'user', 'icon': 'fa-user-plus', 'color': 'cyan', 'message': f"New player registered: {u.full_name} ({u.game_id})"})
    for t in recent_tournaments:
        activity.append({'time': t.date, 'type': 'tournament', 'icon': 'fa-trophy', 'color': 'warning', 'message': f"Tournament scheduled: {t.name} ({t.mode})"})
    for tx in recent_topups:
        activity.append({'time': tx.timestamp, 'type': 'finance', 'icon': 'fa-gem', 'color': 'info', 'message': f"Top‑up: {tx.user.full_name} bought {tx.amount_diamonds}💎 (€{tx.amount_euros})"})
    for tx in recent_cashouts_tx:
        status_tag = f"[{tx.status}]"
        activity.append({'time': tx.timestamp, 'type': 'cashout', 'icon': 'fa-money-bill-wave', 'color': 'orange', 'message': f"Cash‑out {status_tag}: {tx.user.full_name} - {tx.amount_diamonds}💎 (€{tx.amount_euros})"})
    for n in recent_news:
        activity.append({'time': n.created_at, 'type': 'news', 'icon': 'fa-bullhorn', 'color': 'success', 'message': f"News published: {n.title}"})
    
    activity = sorted(activity, key=lambda x: x['time'], reverse=True)[:25]

    # Lists for management tabs
    news_items = PlatformNews.objects.all().order_by('-created_at')
    pending_cashouts = WalletTransaction.objects.filter(transaction_type='CASHOUT', status='Pending').order_by('-timestamp')
    recent_transactions = WalletTransaction.objects.all().order_by('-timestamp')[:20]
    all_tournaments = Tournament.objects.all().order_by('-date')[:25]
    all_users = UserProfile.objects.all().order_by('-created_at')[:40]
    top_players = UserProfile.objects.order_by('-diamonds')[:15]

    context = {
        'total_users': total_users,
        'new_today': new_today,
        'manager_counts': manager_counts,
        'total_managers': total_managers,
        'total_tournaments': total_tournaments,
        'tournament_status': tournament_status,
        'total_matches': total_matches,
        'total_teams': total_teams,
        'total_diamonds': total_diamonds,
        'total_topup': total_topup,
        'total_cashout': total_cashout,
        'total_subscriptions': total_subscriptions,
        'net_revenue': net_revenue,
        'activity': activity,
        'news_items': news_items,
        'pending_cashouts': pending_cashouts,
        'recent_transactions': recent_transactions,
        'all_tournaments': all_tournaments,
        'all_users': all_users,
        'top_players': top_players,
    }
    return render(request, 'tournament/admin_dashboard.html', context)

@login_required
def create_news(request):
    """Create a PlatformNews entry from the admin dashboard."""
    if not request.user.is_staff:
        messages.error(request, "Access denied. Admin rights required.")
        return redirect('home')
    if request.method != 'POST':
        return redirect('admin_dashboard')
    title = request.POST.get('title', '').strip()
    category = request.POST.get('category', 'Update').strip()
    content = request.POST.get('content', '').strip()
    badge = request.POST.get('badge', 'NEW').strip()
    is_published = request.POST.get('is_published') == 'on' or request.POST.get('is_published') == 'true'

    if not title or not content:
        messages.error(request, "Title and Content are required to post news.")
        return redirect('admin_dashboard')
    try:
        PlatformNews.objects.create(
            title=title,
            category=category,
            content=content,
            badge=badge,
            is_published=is_published,
            author=request.user
        )
        messages.success(request, f"News announcement '{title}' published successfully!")
    except Exception as e:
        messages.error(request, f"Failed to create news: {e}")
    return redirect('admin_dashboard')

@login_required
def delete_news(request, news_id):
    """Delete a PlatformNews entry from the admin dashboard."""
    if not request.user.is_staff:
        return redirect('home')
    news = get_object_or_404(PlatformNews, id=news_id)
    title = news.title
    news.delete()
    messages.success(request, f"Announcement '{title}' was deleted.")
    return redirect('admin_dashboard')

@login_required
def process_cashout(request, tx_id, action):
    """Approve or Reject a pending cashout request."""
    if not request.user.is_staff:
        return redirect('home')
    tx = get_object_or_404(WalletTransaction, id=tx_id, transaction_type='CASHOUT')
    if action == 'approve':
        tx.status = 'Completed'
        tx.save()
        messages.success(request, f"Cashout of €{tx.amount_euros} ({tx.amount_diamonds}💎) for {tx.user.full_name} APPROVED.")
    elif action == 'reject':
        tx.status = 'Rejected'
        tx.save()
        # Refund diamonds back to user
        tx.user.diamonds += tx.amount_diamonds
        tx.user.save()
        messages.warning(request, f"Cashout of €{tx.amount_euros} rejected. {tx.amount_diamonds}💎 refunded to {tx.user.full_name}.")
    return redirect('admin_dashboard')

@login_required
def adjust_user_diamonds(request):
    """Admin tool to award or deduct diamonds directly from any user."""
    if not request.user.is_staff:
        return redirect('home')
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        amount = request.POST.get('amount', '0')
        reason = request.POST.get('reason', 'Admin Diamond Adjustment')
        target_user = get_object_or_404(UserProfile, id=user_id)
        try:
            from decimal import Decimal
            delta = Decimal(str(amount))
            target_user.diamonds = max(Decimal('0.00'), target_user.diamonds + delta)
            target_user.save()
            # Log transaction
            tx_type = 'TOPUP' if delta >= 0 else 'CASHOUT'
            WalletTransaction.objects.create(
                user=target_user,
                transaction_type=tx_type,
                amount_diamonds=abs(delta),
                amount_euros=abs(delta),
                description=f"Admin Adjustment: {reason}",
                status='Completed'
            )
            messages.success(request, f"Updated {target_user.full_name}'s balance by {delta:+}💎 (New balance: {target_user.diamonds}💎)")
        except Exception as e:
            messages.error(request, f"Failed to adjust diamonds: {e}")
    return redirect('admin_dashboard')
def leaderboard(request):
    # Annotate teams with scores
    teams_query = Team.objects.annotate(
        total_kills=Sum('scores__kills'),
        total_points=Sum('scores__points'),
        matches_count=Count('scores__match', distinct=True)
    )
    
    teams_list = []
    for team in teams_query:
        teams_list.append({
            'team_name': team.team_name,
            'captain': team.captain.full_name,
            'kills': team.total_kills or 0,
            'points': team.total_points or 0,
            'matches': team.matches_count or 0,
        })
        
    # Sort: Points (desc), then Kills (desc), then name
    teams_list.sort(key=lambda x: (-x['points'], -x['kills'], x['team_name'].lower()))
    
    # Assign ranks
    for index, item in enumerate(teams_list):
        item['rank'] = index + 1
        
    # If leaderboard is empty, generate 10 mock entries
    if not teams_list:
        mock_captains = ["Ahmad", "Faisal", "Kamal", "Zain", "Tariq", "Hassan", "Bilal", "Hamza", "Omar", "Yousef"]
        for idx in range(1, 11):
            teams_list.append({
                'rank': idx,
                'team_name': f"Cyber Elite {idx}",
                'captain': mock_captains[idx - 1],
                'matches': 5,
                'kills': 45 - (idx * 3),
                'points': 120 - (idx * 8),
            })
            
    # Pagination - Top 20 teams
    from django.core.paginator import Paginator
    paginator = Paginator(teams_list, 10)  # 10 teams per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'tournament/leaderboard.html', context)


@login_required
def wallet_view(request):
    transactions = request.user.wallet_transactions.all()
    return render(request, 'tournament/wallet.html', {
        'transactions': transactions,
    })


@login_required
def wallet_topup_view(request):
    if request.method == 'POST':
        amount_str = request.POST.get('amount', '0')
        cardholder_name = request.POST.get('cardholder_name', '').strip()
        card_number = request.POST.get('card_number', '').replace(' ', '')
        expiry_date = request.POST.get('expiry_date', '').strip()
        cvv = request.POST.get('cvv', '').strip()
        
        try:
            amount = float(amount_str)
            if amount < 1.0:
                messages.error(request, "Minimum top-up is 💎1.00 (1 Euro).")
                return redirect('wallet')
        except ValueError:
            messages.error(request, "Invalid amount.")
            return redirect('wallet')
            
        if not cardholder_name or len(card_number) < 15 or not cvv:
            messages.error(request, "Please enter valid payment card details.")
            return redirect('wallet')
            
        from decimal import Decimal
        from .models import PaymentRecord, WalletTransaction
        
        diamond_amount = Decimal(str(amount))
        request.user.diamonds += diamond_amount
        request.user.save()
        
        masked_card = '**** **** **** ' + card_number[-4:]
        PaymentRecord.objects.create(
            user=request.user,
            tier='Diamond Top Up',
            amount=diamond_amount,
            cardholder_name=cardholder_name,
            card_number=masked_card,
            card_expiry=expiry_date,
            cvv='***',
            status='Completed'
        )
        
        WalletTransaction.objects.create(
            user=request.user,
            transaction_type='TOPUP',
            amount_diamonds=diamond_amount,
            amount_euros=diamond_amount,
            description=f'Purchased 💎{diamond_amount} Diamonds via Credit Card',
            status='Completed'
        )
        
        messages.success(request, f"Top Up Successful! 💎{diamond_amount} Diamonds added to your wallet balance.")
        return redirect('wallet')
    return redirect('wallet')


@login_required
def wallet_cashout_view(request):
    if request.method == 'POST':
        amount_str = request.POST.get('amount', '0')
        bank_name = request.POST.get('bank_name', 'Bank').strip()
        account_name = request.POST.get('account_name', '').strip()
        
        try:
            amount = float(amount_str)
            if amount < 1.0:
                messages.error(request, "Minimum cash out is 💎1.00.")
                return redirect('wallet')
        except ValueError:
            messages.error(request, "Invalid amount.")
            return redirect('wallet')
            
        from decimal import Decimal
        diamond_amount = Decimal(str(amount))
        
        if request.user.diamonds < diamond_amount:
            messages.error(request, f"Insufficient balance! You have 💎{request.user.diamonds}, but tried to cash out 💎{diamond_amount}.")
            return redirect('wallet')
            
        request.user.diamonds -= diamond_amount
        request.user.save()
        
        from .models import WalletTransaction
        WalletTransaction.objects.create(
            user=request.user,
            transaction_type='CASHOUT',
            amount_diamonds=-diamond_amount,
            amount_euros=diamond_amount,
            description=f'Real Money Cash Out (€{diamond_amount}) to {bank_name} ({account_name})',
            status='Completed'
        )
        
        messages.success(request, f"Cash Out Processed! 💎{diamond_amount} (€{diamond_amount}) transferred to your account.")
        return redirect('wallet')
    return redirect('wallet')


@login_required
def become_manager(request):
    user = request.user
    
    # Block active managers from upgrading again until expiration
    if user.active_membership_tier:
        messages.info(request, "You are already a Tournament Manager! This option will return once your current 1-month membership expires.")
        return redirect('home')

    if request.method == 'POST':
        tier = request.POST.get('tier')
        
        if tier not in ['Silver', 'Gold', 'Diamond']:
            messages.error(request, "Invalid membership tier selection.")
            return redirect('become_manager')
            
        from decimal import Decimal
        from .models import PaymentRecord, WalletTransaction
        
        amount = Decimal(str(PaymentRecord.TIER_PRICES.get(tier, 0.00)))
        
        if user.diamonds < amount:
            messages.error(request, f"Insufficient Diamonds balance! You need 💎{amount} but have 💎{user.diamonds}. Please top up your wallet.")
            return redirect('wallet')
            
        # Deduct Diamonds from User balance
        user.diamonds -= amount
        
        # Save PaymentRecord & WalletTransaction
        PaymentRecord.objects.create(
            user=user,
            tier=tier,
            amount=amount,
            cardholder_name=user.full_name,
            card_number='Paid via 💎 Wallet',
            card_expiry='--/--',
            cvv='***',
            status='Completed',
        )
        
        WalletTransaction.objects.create(
            user=user,
            transaction_type='SUBSCRIPTION',
            amount_diamonds=-amount,
            amount_euros=amount,
            description=f'Upgraded to {tier} Manager Tier (💎{amount})',
            status='Completed'
        )
        
        # Upgrade the user
        from django.utils import timezone
        user.membership_tier = tier
        user.membership_upgraded_at = timezone.now()
        user.save()
        
        messages.success(request, f"Payment successful! You are now upgraded to a {tier} Manager for 1 month (💎{amount} deducted).")
        return redirect('my_tournaments')
        
    return render(request, 'tournament/become_manager.html')


@login_required
def create_team(request):
    tournaments = Tournament.objects.filter(status='Upcoming', slots_available__gt=0)
    
    if request.method == 'POST':
        tournament_id = request.POST.get('tournament')
        team_name = request.POST.get('team_name')
        
        try:
            tournament = Tournament.objects.get(id=tournament_id)
        except Tournament.DoesNotExist:
            messages.error(request, "Selected tournament does not exist.")
            return render(request, 'tournament/create_team.html', {'tournaments': tournaments})

        mode = tournament.mode  # 'Solo', 'Duo', 'Squad', '1v1', '2v2'
        
        # Extract players dynamically based on Mode
        players = []
        p1_name = request.POST.get('player_1_name', request.user.full_name)
        p1_fid = request.POST.get('player_1_id', request.user.game_id)
        if p1_name and p1_fid:
            players.append({'role': 'Solo Player' if mode in ['Solo', '1v1'] else 'Captain / Player 1', 'name': p1_name, 'free_fire_id': p1_fid})

        if mode in ['Duo', '2v2', 'Squad']:
            p2_name = request.POST.get('player_2_name')
            p2_fid = request.POST.get('player_2_id')
            if p2_name and p2_fid:
                players.append({'role': 'Teammate / Player 2', 'name': p2_name, 'free_fire_id': p2_fid})

        if mode in ['Squad']:
            for i in [3, 4]:
                p_name = request.POST.get(f'player_{i}_name')
                p_fid = request.POST.get(f'player_{i}_id')
                if p_name and p_fid:
                    players.append({'role': f'Main Player {i}', 'name': p_name, 'free_fire_id': p_fid})
            
            sub_name = request.POST.get('sub_name')
            sub_fid = request.POST.get('sub_id')
            if sub_name and sub_fid:
                players.append({'role': 'Substitute', 'name': sub_name, 'free_fire_id': sub_fid})

        # Validate minimum player count according to format
        min_required = 1 if mode in ['Solo', '1v1'] else (2 if mode in ['Duo', '2v2'] else 4)
        if not team_name or len(players) < min_required:
            messages.error(request, f"Please provide all required player details for {mode} format ({min_required} player(s) required).")
            return render(request, 'tournament/create_team.html', {'tournaments': tournaments})

        from decimal import Decimal
        from .models import PaymentRecord, WalletTransaction
        fee_amount = Decimal(str(tournament.entry_fee))
        
        # Check Diamond Balance
        if request.user.diamonds < fee_amount:
            messages.error(request, f"Insufficient Diamonds balance! Entry fee is 💎{fee_amount}, but you have 💎{request.user.diamonds}. Please top up your wallet.")
            return redirect('wallet')

        # Deduct entry fee from user wallet
        request.user.diamonds -= fee_amount
        request.user.save()

        PaymentRecord.objects.create(
            user=request.user,
            tier='Entry Fee',
            amount=fee_amount,
            cardholder_name=request.user.full_name,
            card_number='Paid via 💎 Wallet',
            card_expiry='--/--',
            cvv='***',
            status='Completed'
        )
        
        WalletTransaction.objects.create(
            user=request.user,
            transaction_type='ENTRY_FEE',
            amount_diamonds=-fee_amount,
            amount_euros=fee_amount,
            description=f'Entry Fee for {tournament.name} (💎{fee_amount})',
            status='Completed'
        )
        
        # Create team with Paid status
        team = Team.objects.create(
            tournament=tournament,
            team_name=team_name,
            captain=request.user,
            players=players,
            payment_status='Paid'
        )
        
        # Update slots available
        tournament.slots_available = max(0, tournament.slots_available - 1)
        tournament.save()
        
        import datetime
        from django.utils import timezone
        now = timezone.now()
        unlock_time = tournament.date - datetime.timedelta(minutes=5)
        is_unlocked = (now >= unlock_time)
        
        room_credentials = {
            'tournament_name': tournament.name,
            'team_name': team_name,
            'custom_room_id': tournament.custom_room_id,
            'custom_room_password': tournament.custom_room_password,
            'entry_fee': str(tournament.entry_fee),
            'is_unlocked': is_unlocked,
            'unlock_time_iso': unlock_time.isoformat(),
            'tournament_date_formatted': tournament.date.strftime('%b %d, %Y at %H:%M')
        }
        
        messages.success(request, f"Payment confirmed! '{team_name}' has joined '{tournament.name}' (💎{fee_amount} deducted).")
        return render(request, 'tournament/create_team.html', {
            'tournaments': tournaments,
            'joined_success': True,
            'room_credentials': room_credentials
        })
        
    return render(request, 'tournament/create_team.html', {'tournaments': tournaments})


@login_required
def my_tournaments_view(request):
    user = request.user
    tier = user.active_membership_tier
    
    # Calculate daily creation stats
    from django.utils import timezone
    import datetime
    today = timezone.now().date()
    today_start = timezone.make_aware(datetime.datetime.combine(today, datetime.time.min))
    today_end = timezone.make_aware(datetime.datetime.combine(today, datetime.time.max))
    hosted_today_count = Tournament.objects.filter(creator=user, date__range=(today_start, today_end)).count()
    
    limit = 0
    if tier == 'Silver':
        limit = 1
    elif tier == 'Gold':
        limit = 3
    elif tier == 'Diamond':
        limit = 10
        
    is_limit_reached = (hosted_today_count >= limit) if limit > 0 else (not tier)

    captained_teams = Team.objects.filter(captain=user)
    
    now = timezone.now()
    played_tournaments = []
    for team in captained_teams:
        t = team.tournament
        score = Score.objects.filter(team=team).first()
        if score:
            result = "Won" if score.placement == 1 else "Lost"
        else:
            result = "Pending"
            
        hosted_by = t.creator.full_name if t.creator else "System Admin"
        unlock_time = t.date - datetime.timedelta(minutes=5)
        is_unlocked = (now >= unlock_time)
        
        played_tournaments.append({
            'tournament': t,
            'hosted_by': hosted_by,
            'result': result,
            'entry_fee': t.entry_fee,
            'custom_room_id': t.custom_room_id,
            'custom_room_password': t.custom_room_password,
            'is_unlocked': is_unlocked,
            'unlock_time_iso': unlock_time.isoformat(),
            'match_date_formatted': t.date.strftime('%b %d, %H:%M'),
        })
        
    hosted_tournaments = Tournament.objects.filter(creator=user).order_by('-date')
    hosted_data = []
    for t in hosted_tournaments:
        final_match = Match.objects.filter(tournament=t, status='Completed').order_by('-match_time').first()
        winner_name = final_match.winner.team_name if (final_match and final_match.winner) else "TBD"
        
        hosted_data.append({
            'id': t.id,
            'tournament': t,
            'winner': winner_name,
            'entry_fee': t.entry_fee,
            'mode': t.mode,
            'prize_money': t.prize_pool,
            'status': t.status,
            'raw_date': t.date.strftime('%Y-%m-%dT%H:%M') if t.date else '',
            'custom_room_id': t.custom_room_id,
            'custom_room_password': t.custom_room_password,
            'teams': list(t.teams.all()),
        })
        
    return render(request, 'tournament/my_tournaments.html', {
        'played_tournaments': played_tournaments,
        'hosted_tournaments': hosted_data,
        'hosted_today_count': hosted_today_count,
        'limit': limit,
        'is_limit_reached': is_limit_reached,
        'tier': tier,
    })


@login_required
def edit_tournament_view(request, tournament_id):
    user = request.user
    tournament = get_object_or_404(Tournament, id=tournament_id)
    
    if tournament.creator != user and not user.is_staff:
        messages.error(request, "You do not have permission to edit this tournament.")
        return redirect('my_tournaments')
        
    if request.method == 'POST':
        date_time_str = request.POST.get('date_time')
        mode = request.POST.get('mode')
        entry_fee_str = request.POST.get('entry_fee')
        custom_room_id = request.POST.get('custom_room_id', '').strip()
        custom_room_password = request.POST.get('custom_room_password', '').strip()
        
        if mode not in ['Solo', 'Duo', 'Squad']:
            messages.error(request, "Invalid tournament type. Choose Solo, Duo, or Squad.")
            return redirect('my_tournaments')
            
        from django.utils.dateparse import parse_datetime
        from django.utils import timezone
        import datetime
        
        date_time_parsed = parse_datetime(date_time_str)
        if not date_time_parsed:
            try:
                date_time_parsed = datetime.datetime.strptime(date_time_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                messages.error(request, "Invalid Date & Time format.")
                return redirect('my_tournaments')
                
        if timezone.is_naive(date_time_parsed):
            date_time_parsed = timezone.make_aware(date_time_parsed)
            
        tier = user.active_membership_tier
        try:
            fee = float(entry_fee_str)
        except (ValueError, TypeError):
            messages.error(request, "Invalid participation fee value.")
            return redirect('my_tournaments')
            
        max_fee = 0.0
        if tier == 'Silver':
            max_fee = 2.0
        elif tier == 'Gold':
            max_fee = 5.0
        elif tier == 'Diamond':
            max_fee = 10.0
            
        if fee > max_fee:
            messages.error(request, f"Participation fee too high! As a {tier} Manager, your limit is €{max_fee}.")
            return redirect('my_tournaments')
            
        tournament.date = date_time_parsed
        tournament.mode = mode
        tournament.entry_fee = fee
        tournament.prize_pool = fee * 40
        tournament.name = f"{user.full_name}'s {mode} Clash"
        if custom_room_id:
            tournament.custom_room_id = custom_room_id
        if custom_room_password:
            tournament.custom_room_password = custom_room_password
        tournament.save()
        
        messages.success(request, f"Tournament '{tournament.name}' updated successfully!")
        return redirect('my_tournaments')
        
    return redirect('my_tournaments')


@login_required
def delete_tournament_view(request, tournament_id):
    user = request.user
    tournament = get_object_or_404(Tournament, id=tournament_id)
    
    if tournament.creator != user and not user.is_staff:
        messages.error(request, "You do not have permission to delete this tournament.")
        return redirect('my_tournaments')
        
    if request.method == 'POST':
        t_name = tournament.name
        tournament.delete()
        messages.success(request, f"Tournament '{t_name}' deleted successfully!")
        return redirect('my_tournaments')
        
    return redirect('my_tournaments')


@login_required
def complete_tournament_view(request, tournament_id):
    """Host declares the winner of a tournament – saves Match, Score, credits prize."""
    user = request.user
    tournament = get_object_or_404(Tournament, id=tournament_id)

    if tournament.creator != user and not user.is_staff:
        messages.error(request, "You do not have permission to complete this tournament.")
        return redirect('my_tournaments')

    if tournament.status == 'Completed':
        messages.warning(request, "This tournament has already been completed.")
        return redirect('my_tournaments')

    if request.method == 'POST':
        team_id = request.POST.get('winner_team_id')
        kills_str = request.POST.get('kills', '0')
        award_prize = request.POST.get('award_prize') == 'on'

        if not team_id:
            messages.error(request, "Please select a winning team.")
            return redirect('my_tournaments')

        try:
            kills = max(0, int(kills_str))
        except (ValueError, TypeError):
            kills = 0

        winner_team = get_object_or_404(Team, id=team_id, tournament=tournament)

        # Points: 12 placement (Booyah) + 1 per kill
        total_points = 12 + kills

        from decimal import Decimal

        # Create or get the Match record
        match, _ = Match.objects.get_or_create(
            tournament=tournament,
            defaults={
                'match_time': timezone.now(),
                'status': 'Completed',
                'winner': winner_team,
                'map_name': 'Bermuda',
            }
        )
        match.status = 'Completed'
        match.winner = winner_team
        match.match_time = timezone.now()
        match.save()

        # Create Score for winner
        Score.objects.update_or_create(
            match=match,
            team=winner_team,
            defaults={
                'kills': kills,
                'placement': 1,
                'points': total_points,
            }
        )

        # Mark tournament completed
        tournament.status = 'Completed'
        tournament.save()

        # Award prize pool diamonds to the winner captain's wallet
        if award_prize and tournament.prize_pool > 0:
            captain = winner_team.captain
            prize = Decimal(str(tournament.prize_pool))
            captain.diamonds += prize
            captain.save()

            WalletTransaction.objects.create(
                user=captain,
                transaction_type='PRIZE_WIN',
                amount_diamonds=prize,
                amount_euros=prize,
                description=f"🏆 Tournament Win: {tournament.name} – 1st Place ({kills} kills, {total_points} pts)",
                status='Completed'
            )

        messages.success(
            request,
            f"🏆 Tournament '{tournament.name}' completed! Winner: {winner_team.team_name} "
            f"({kills} kills, {total_points} pts)"
        )
        return redirect('my_tournaments')

    return redirect('my_tournaments')


@login_required
def create_tournament_view(request):
    user = request.user
    tier = user.active_membership_tier
    
    # Block standard players and expired memberships
    if tier not in ['Silver', 'Gold', 'Diamond']:
        messages.error(request, "Only active Silver, Gold, or Diamond Managers can host tournaments. Upgrade now!")
        return redirect('become_manager')
        
    if request.method == 'POST':
        date_time_str = request.POST.get('date_time')
        mode = request.POST.get('mode')
        entry_fee_str = request.POST.get('entry_fee')
        custom_room_id = request.POST.get('custom_room_id', '').strip()
        custom_room_password = request.POST.get('custom_room_password', '').strip()
        
        # Validate mode is Solo, Duo, or Squad
        if mode not in ['Solo', 'Duo', 'Squad']:
            messages.error(request, "Invalid tournament type. Choose Solo, Duo, or Squad.")
            return redirect('my_tournaments')
        
        # Parse datetime
        from django.utils.dateparse import parse_datetime
        from django.utils import timezone
        import datetime
        
        date_time_parsed = parse_datetime(date_time_str)
        if not date_time_parsed:
            try:
                date_time_parsed = datetime.datetime.strptime(date_time_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                messages.error(request, "Invalid Date & Time format.")
                return redirect('my_tournaments')
                
        if timezone.is_naive(date_time_parsed):
            date_time_parsed = timezone.make_aware(date_time_parsed)
            
        # Daily limit check
        today = timezone.now().date()
        today_start = timezone.make_aware(datetime.datetime.combine(today, datetime.time.min))
        today_end = timezone.make_aware(datetime.datetime.combine(today, datetime.time.max))
        hosted_today_count = Tournament.objects.filter(creator=user, date__range=(today_start, today_end)).count()
        
        limit = 0
        if tier == 'Silver':
            limit = 1
        elif tier == 'Gold':
            limit = 3
        elif tier == 'Diamond':
            limit = 10
            
        if hosted_today_count >= limit:
            messages.error(request, f"Daily limit reached! As a {tier} Manager, you can only host {limit} tournament(s) per 24 hours. Please wait 24 hours to create another one.")
            return redirect('my_tournaments')
            
        # Fee validation
        try:
            fee = float(entry_fee_str)
        except (ValueError, TypeError):
            messages.error(request, "Invalid participation fee value.")
            return redirect('my_tournaments')
            
        max_fee = 0.0
        if tier == 'Silver':
            max_fee = 2.0
        elif tier == 'Gold':
            max_fee = 5.0
        elif tier == 'Diamond':
            max_fee = 10.0
            
        if fee > max_fee:
            messages.error(request, f"Participation fee too high! As a {tier} Manager, your limit is €{max_fee}.")
            return redirect('my_tournaments')
            
        # Save new tournament
        t_name = f"{user.full_name}'s {mode} Clash"
        calculated_prize = fee * 40
        
        t = Tournament(
            name=t_name,
            mode=mode,
            date=date_time_parsed,
            entry_fee=fee,
            prize_pool=calculated_prize,
            slots_total=20,
            slots_available=20,
            status='Upcoming',
            creator=user
        )
        if custom_room_id:
            t.custom_room_id = custom_room_id
        if custom_room_password:
            t.custom_room_password = custom_room_password
        t.save()
        
        messages.success(request, f"Tournament '{t_name}' created successfully!")
        return redirect('my_tournaments')
        
    # GET request – redirect to my tournaments page (the form is now a modal there)
    return redirect('my_tournaments')


def serve_ff_banner(request):
    candidates = [
        r"C:\Users\ehsan\.gemini\antigravity\brain\f27ecd35-fec8-43e5-af73-c5b8b4bb0fd8\.user_uploaded\media_1790003454756.png",
        r"C:\Users\ehsan\.gemini\antigravity\brain\f27ecd35-fec8-43e5-af73-c5b8b4bb0fd8\.user_uploaded\media_1790002682534.png",
        r"C:\Users\ehsan\.gemini\antigravity\brain\f27ecd35-fec8-43e5-af73-c5b8b4bb0fd8\.user_uploaded\media_1788363650843.png",
    ]
    for p in candidates:
        if os.path.exists(p):
            return FileResponse(open(p, 'rb'), content_type='image/png')
    raise Http404("Banner not found")

