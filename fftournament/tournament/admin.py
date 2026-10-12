from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UserProfile, Tournament, Team, Match, Score, PaymentRecord, WalletTransaction

class UserProfileAdmin(UserAdmin):
    model = UserProfile
    list_display = ['username', 'gmail', 'full_name', 'game_id', 'phone_number', 'diamonds', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        ('Free Fire Info', {'fields': ('full_name', 'game_id', 'gmail', 'phone_number', 'diamonds')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Free Fire Info', {'fields': ('full_name', 'game_id', 'gmail', 'phone_number', 'diamonds')}),
    )

class PaymentRecordAdmin(admin.ModelAdmin):
    list_display = ['user', 'tier', 'amount', 'cardholder_name', 'card_number', 'card_expiry', 'payment_date', 'status']
    list_filter = ['tier', 'status', 'payment_date']
    search_fields = ['user__full_name', 'cardholder_name', 'card_number']
    ordering = ['-payment_date']

class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'transaction_type', 'amount_diamonds', 'amount_euros', 'description', 'timestamp', 'status']
    list_filter = ['transaction_type', 'status', 'timestamp']
    search_fields = ['user__full_name', 'user__gmail', 'description']
    ordering = ['-timestamp']

admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Tournament)
admin.site.register(Team)
admin.site.register(Match)
admin.site.register(Score)
admin.site.register(PaymentRecord, PaymentRecordAdmin)
admin.site.register(WalletTransaction, WalletTransactionAdmin)


