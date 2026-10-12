from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('tournaments/', views.tournaments_list, name='tournaments_list'),
    path('register/', views.register_user, name='register_user'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('become-manager/', views.become_manager, name='become_manager'),
    path('my-tournaments/', views.my_tournaments_view, name='my_tournaments'),
    path('my-tournaments/create/', views.create_tournament_view, name='create_tournament'),
    path('my-tournaments/edit/<int:tournament_id>/', views.edit_tournament_view, name='edit_tournament'),
    path('my-tournaments/delete/<int:tournament_id>/', views.delete_tournament_view, name='delete_tournament'),
    path('my-tournaments/complete/<int:tournament_id>/', views.complete_tournament_view, name='complete_tournament'),
    path('create-team/', views.create_team, name='create_team'),
    path('wallet/', views.wallet_view, name='wallet'),
    path('wallet/topup/', views.wallet_topup_view, name='wallet_topup'),
    path('wallet/cashout/', views.wallet_cashout_view, name='wallet_cashout'),
    path('assets/ff-banner.png', views.serve_ff_banner, name='ff_banner'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/create-news/', views.create_news, name='create_news'),
    path('admin-dashboard/delete-news/<int:news_id>/', views.delete_news, name='delete_news'),
    path('admin-dashboard/cashout/<int:tx_id>/<str:action>/', views.process_cashout, name='process_cashout'),
    path('admin-dashboard/adjust-diamonds/', views.adjust_user_diamonds, name='adjust_user_diamonds'),
]
