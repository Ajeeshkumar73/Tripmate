from django.urls import path
from . import views
from . import api_views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # ── Page Views ──────────────────────────────────────────────────────────
    path('', views.landing_page, name='Landing_page'),
    path('login/', views.login_page, name='Login_page'),
    path('register/', views.register_page, name='register_page'),
    path('logout/', views.logout_view, name='Logout'),
    path('userpage/', views.user_dashboard, name='user_page'),
    path('trips/', views.trips_page, name='trips_page'),
    path('trips/<int:trip_id>/', views.trip_detail_page, name='trip_detail'),
    path('trips/<int:trip_id>/summary/', views.trip_summary_page, name='trip_summary'),
    path('ai-planner/', views.ai_planner_page, name='ai_planner'),
    path('map/', views.map_explorer_page, name='map_explorer'),
    path('destinations/', views.destination_explorer_page, name='destination_explorer'),
    path('budget/', views.budget_planner_page, name='budget_planner'),
    path('expenses/', views.expenses_page, name='expenses'),
    path('weather/', views.weather_page, name='weather'),
    path('chatbot/', views.chatbot_page, name='chatbot'),
    path('packing/', views.packing_page, name='packing'),
    path('wallet/', views.wallet_page, name='wallet'),
    path('journal/', views.journal_page, name='journal'),
    path('emergency/', views.emergency_page, name='emergency'),
    path('profile/', views.profile_page, name='profile'),
    path('social/', views.social_page, name='social'),
    path('admin-dashboard/', views.admin_dashboard_page, name='admin_dashboard'),

    # ── API: Auth ────────────────────────────────────────────────────────────
    path('api/auth/register/', api_views.RegisterAPIView.as_view(), name='api_register'),
    path('api/auth/login/', api_views.LoginAPIView.as_view(), name='api_login'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/profile/', api_views.ProfileAPIView.as_view(), name='api_profile'),

    # ── API: Trips ────────────────────────────────────────────────────────────
    path('api/trips/', api_views.TripListCreateAPIView.as_view(), name='api_trips'),
    path('api/trips/<int:pk>/', api_views.TripDetailAPIView.as_view(), name='api_trip_detail'),

    # ── API: AI ───────────────────────────────────────────────────────────────
    path('api/ai/generate-itinerary/', api_views.GenerateItineraryAPIView.as_view(), name='api_generate_itinerary'),
    path('api/ai/chat/', api_views.ChatAPIView.as_view(), name='api_chat'),

    # ── API: Weather ──────────────────────────────────────────────────────────
    path('api/weather/', api_views.WeatherAPIView.as_view(), name='api_weather'),

    # ── API: Nearby ───────────────────────────────────────────────────────────
    path('api/nearby/', api_views.NearbyAPIView.as_view(), name='api_nearby'),

    # ── API: Expenses ─────────────────────────────────────────────────────────
    path('api/expenses/', api_views.ExpenseListCreateAPIView.as_view(), name='api_expenses'),
    path('api/expenses/<int:pk>/', api_views.ExpenseDetailAPIView.as_view(), name='api_expense_detail'),
    path('api/expenses/summary/', api_views.ExpenseSummaryAPIView.as_view(), name='api_expense_summary'),

    # ── API: Budget ───────────────────────────────────────────────────────────
    path('api/budget/<int:trip_id>/', api_views.BudgetAPIView.as_view(), name='api_budget'),

    # ── API: Packing ──────────────────────────────────────────────────────────
    path('api/packing/<int:trip_id>/', api_views.PackingListAPIView.as_view(), name='api_packing'),

    # ── API: Documents ────────────────────────────────────────────────────────
    path('api/documents/', api_views.TravelDocumentListCreateAPIView.as_view(), name='api_documents'),
    path('api/documents/<int:pk>/', api_views.TravelDocumentDetailAPIView.as_view(), name='api_document_detail'),

    # ── API: Journal ──────────────────────────────────────────────────────────
    path('api/journal/', api_views.JournalListCreateAPIView.as_view(), name='api_journal'),
    path('api/journal/<int:pk>/', api_views.JournalDetailAPIView.as_view(), name='api_journal_detail'),

    # ── API: Notifications ────────────────────────────────────────────────────
    path('api/notifications/', api_views.NotificationAPIView.as_view(), name='api_notifications'),

    # ── API: Bookmarks ────────────────────────────────────────────────────────
    path('api/bookmarks/', api_views.BookmarkListCreateAPIView.as_view(), name='api_bookmarks'),
    path('api/bookmarks/<int:pk>/', api_views.BookmarkDetailAPIView.as_view(), name='api_bookmark_detail'),

    # ── API: Emergency Contacts ───────────────────────────────────────────────
    path('api/emergency-contacts/', api_views.EmergencyContactAPIView.as_view(), name='api_emergency_contacts'),
    path('api/emergency-contacts/<int:pk>/', api_views.EmergencyContactDetailAPIView.as_view(), name='api_emergency_contact_detail'),

    # ── API: Reviews ──────────────────────────────────────────────────────────
    path('api/reviews/', api_views.ReviewListCreateAPIView.as_view(), name='api_reviews'),

    # ── API: Photos ───────────────────────────────────────────────────────────
    path('api/photos/', api_views.PhotoListCreateAPIView.as_view(), name='api_photos'),

    # ── API: Trip Summary ─────────────────────────────────────────────────────
    path('api/trips/<int:trip_id>/summary/', api_views.TripSummaryAPIView.as_view(), name='api_trip_summary'),

    # ── API: Dashboard Stats ──────────────────────────────────────────────────
    path('api/dashboard/', api_views.DashboardStatsAPIView.as_view(), name='api_dashboard'),

    # ── API: Admin ────────────────────────────────────────────────────────────
    path('api/admin/dashboard/', api_views.AdminDashboardAPIView.as_view(), name='api_admin_dashboard'),

    # ── API: Geocode & Route ──────────────────────────────────────────────────
    path('api/geocode/', api_views.GeocodeAPIView.as_view(), name='api_geocode'),
    path('api/route/', api_views.RouteAPIView.as_view(), name='api_route'),

    # ── API: Destinations ─────────────────────────────────────────────────────
    path('api/destinations/', api_views.DestinationListAPIView.as_view(), name='api_destinations'),
]