from django.apps import AppConfig


class TournamentConfig(AppConfig):
    name = 'tournament'

    def ready(self):
        # 0. Apply safe SQLite DecimalField converter patch to prevent decimal.InvalidOperation
        try:
            import decimal
            from django.db.backends.sqlite3.operations import DatabaseOperations
            from django.db.models.expressions import Col

            def safe_get_decimalfield_converter(self, expression):
                create_decimal = decimal.Context(prec=15).create_decimal_from_float
                if isinstance(expression, Col):
                    quantize_value = decimal.Decimal(1).scaleb(
                        -expression.output_field.decimal_places
                    )

                    def converter(value, expression, connection):
                        if value is not None:
                            try:
                                if isinstance(value, (int, float)):
                                    dec = create_decimal(value)
                                else:
                                    dec = decimal.Decimal(str(value))
                                return dec.quantize(
                                    quantize_value, context=expression.output_field.context
                                )
                            except (decimal.InvalidOperation, TypeError, ValueError):
                                try:
                                    return decimal.Decimal(str(value)).quantize(quantize_value)
                                except Exception:
                                    return decimal.Decimal("0.00")
                else:
                    def converter(value, expression, connection):
                        if value is not None:
                            try:
                                if isinstance(value, (int, float)):
                                    return create_decimal(value)
                                return decimal.Decimal(str(value))
                            except (decimal.InvalidOperation, TypeError, ValueError):
                                try:
                                    return decimal.Decimal(str(value))
                                except Exception:
                                    return decimal.Decimal("0.00")

                return converter

            DatabaseOperations.get_decimalfield_converter = safe_get_decimalfield_converter
        except Exception:
            pass

        try:
            from django.db import connection
            with connection.cursor() as cursor:
                # 1. Check if 'diamonds' column exists in 'tournament_userprofile'
                cursor.execute("PRAGMA table_info(tournament_userprofile);")
                columns = [row[1] for row in cursor.fetchall()]
                if columns and 'diamonds' not in columns:
                    cursor.execute("ALTER TABLE tournament_userprofile ADD COLUMN diamonds decimal(12, 2) NOT NULL DEFAULT 100.00;")
                
                # Ensure all users have valid numeric diamonds
                cursor.execute("UPDATE tournament_userprofile SET diamonds = 100.00 WHERE diamonds IS NULL OR diamonds = '' OR diamonds = 'None';")
                
                # 2. Check if 'tournament_wallettransaction' table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tournament_wallettransaction';")
                if not cursor.fetchone():
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS "tournament_wallettransaction" (
                            "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                            "transaction_type" varchar(20) NOT NULL,
                            "amount_diamonds" decimal(12, 2) NOT NULL,
                            "amount_euros" decimal(12, 2) NOT NULL,
                            "description" varchar(255) NOT NULL,
                            "timestamp" datetime NOT NULL,
                            "status" varchar(20) NOT NULL,
                            "user_id" bigint NOT NULL REFERENCES "tournament_userprofile" ("id") DEFERRABLE INITIALLY DEFERRED
                        );
                    """)
                    cursor.execute("CREATE INDEX IF NOT EXISTS 'tournament_wallettransaction_user_id_idx' ON 'tournament_wallettransaction' ('user_id');")
                
                # 3. Check if 'tournament_platformnews' table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tournament_platformnews';")
                if not cursor.fetchone():
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS "tournament_platformnews" (
                            "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                            "title" varchar(200) NOT NULL,
                            "category" varchar(30) NOT NULL,
                            "content" text NOT NULL,
                            "badge" varchar(30) NOT NULL,
                            "created_at" datetime NOT NULL,
                            "is_published" bool NOT NULL,
                            "author_id" bigint REFERENCES "tournament_userprofile" ("id") DEFERRABLE INITIALLY DEFERRED
                        );
                    """)
                    cursor.execute("CREATE INDEX IF NOT EXISTS 'tournament_platformnews_author_id_idx' ON 'tournament_platformnews' ('author_id');")
        except Exception:
            pass

        # Ensure admin user and seed news
        try:
            from .models import UserProfile, PlatformNews
            from django.db.models import Q
            from django.utils import timezone

            admin_user = UserProfile.objects.filter(
                Q(email__iexact='admin@gmail.com') |
                Q(gmail__iexact='admin@gmail.com') |
                Q(username__iexact='admin')
            ).first()

            if not admin_user:
                admin_user = UserProfile.objects.create(
                    username='admin',
                    email='admin@gmail.com',
                    gmail='admin@gmail.com',
                    full_name='System Admin',
                    game_id='ADMIN-001',
                    phone_number='+1000000000',
                    is_staff=True,
                    is_superuser=True,
                    diamonds=Decimal('999999.00'),
                    membership_tier='Diamond',
                    membership_upgraded_at=timezone.now()
                )
                admin_user.set_password('100122')
                admin_user.save()
            else:
                updated = False
                if not admin_user.is_staff or not admin_user.is_superuser:
                    admin_user.is_staff = True
                    admin_user.is_superuser = True
                    updated = True
                if admin_user.email != 'admin@gmail.com' or admin_user.gmail != 'admin@gmail.com':
                    admin_user.email = 'admin@gmail.com'
                    admin_user.gmail = 'admin@gmail.com'
                    updated = True
                if not admin_user.check_password('100122'):
                    admin_user.set_password('100122')
                    updated = True
                if updated:
                    admin_user.save()

            # Seed default news if empty
            if PlatformNews.objects.count() == 0:
                PlatformNews.objects.create(
                    title="Free Fire Grand Masters Tournament Series 2026",
                    category="Event",
                    badge="HOT",
                    content="Registration is now officially open for Solo, Duo, and Squad brackets. Compete for the massive prize pool with real-time room key distribution!",
                    author=admin_user,
                    is_published=True
                )
                PlatformNews.objects.create(
                    title="Anti-Cheat & Fair Play Protocol v2.5 Deployed",
                    category="Update",
                    badge="NEW",
                    content="Our automated game ID verification and custom room referee monitoring system has been upgraded to guarantee 100% fair matches.",
                    author=admin_user,
                    is_published=True
                )
                PlatformNews.objects.create(
                    title="Instant Diamond Payouts & VIP Manager Dashboard",
                    category="Announcement",
                    badge="FEATURE",
                    content="Diamond currency cash-outs to real Euros are now processed with priority banking. VIP managers can host custom clash rooms daily.",
                    author=admin_user,
                    is_published=True
                )
        except Exception:
            pass

