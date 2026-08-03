import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .models import (
    Trip, Destination, Itinerary, Expense, Budget, Notification,
    ChatHistory, PackingList, TravelDocument, TravelJournal,
    EmergencyContact, Review, Photo, UserProfile, Bookmark
)
from .services.geocode import get_coordinates
from .services.routing import get_route


# ─── Landing Page ─────────────────────────────────────────────────────────────
def landing_page(request):
    # Handle review POST from authenticated users
    if request.method == 'POST' and request.user.is_authenticated:
        title = request.POST.get('review_title', '').strip()
        content = request.POST.get('review_content', '').strip()
        rating = int(request.POST.get('review_rating', 5))
        if title and content and 1 <= rating <= 5:
            Review.objects.create(
                user=request.user,
                title=title,
                content=content,
                rating=rating,
                is_public=True,
            )
            messages.success(request, 'Your review has been posted! Thank you 🌟')
        else:
            messages.error(request, 'Please fill in all review fields.')
        return redirect('Landing_page')

    destinations = Destination.objects.filter(is_trending=True)[:6]
    reviews = Review.objects.filter(is_public=True, is_reported=False).order_by('-created_at')[:9]
    return render(request, 'landing_page.html', {
        'destinations': destinations,
        'reviews': reviews,
    })


# ─── Auth Views ───────────────────────────────────────────────────────────────
def login_page(request):
    if request.user.is_authenticated:
        return redirect('user_page')
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user_obj = User.objects.filter(email=email).first()
        if user_obj is None:
            messages.error(request, "Email not registered.")
            return render(request, 'login_page.html')
        user = authenticate(request, username=user_obj.username, password=password)
        if user:
            login(request, user)
            messages.success(request, "Welcome back! You're logged in.")
            next_url = request.GET.get('next', 'user_page')
            return redirect(next_url)
        else:
            messages.error(request, "Invalid email or password.")
    return render(request, 'login_page.html')


def register_page(request):
    if request.user.is_authenticated:
        return redirect('user_page')
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm = request.POST.get('confirm_password')

        if password != confirm:
            messages.error(request, "Passwords do not match.")
            return render(request, 'register_page.html')
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return render(request, 'register_page.html')
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return render(request, 'register_page.html')

        user = User.objects.create_user(username=username, email=email, password=password)
        UserProfile.objects.get_or_create(user=user)
        messages.success(request, "Account created! Please login.")
        return redirect('Login_page')
    return render(request, 'register_page.html')


def logout_view(request):
    logout(request)
    request.session.flush()
    messages.success(request, "You've been logged out. Safe travels! ✈️")
    return redirect('Landing_page')


# ─── User Dashboard ───────────────────────────────────────────────────────────
@login_required(login_url='/login/')
def user_dashboard(request):
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)
    trips = Trip.objects.filter(user=user).order_by('-created_at')
    upcoming_trips = trips.filter(status__in=['upcoming', 'planning'])[:3]
    recent_expenses = Expense.objects.filter(user=user).order_by('-date')[:5]
    notifications = Notification.objects.filter(user=user, is_read=False)[:5]
    bookmarks = Bookmark.objects.filter(user=user)[:4]

    # Stats
    total_spent = sum(e.amount for e in Expense.objects.filter(user=user))

    context = {
        'profile': profile,
        'upcoming_trips': upcoming_trips,
        'total_trips': trips.count(),
        'total_spent': total_spent,
        'recent_expenses': recent_expenses,
        'notifications': notifications,
        'bookmarks': bookmarks,
        'unread_count': notifications.count(),
    }

    # Handle trip creation from form
    if request.method == 'POST':
        source = request.POST.get("start_point")
        destination = request.POST.get("end_point")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        budget = request.POST.get("budget")
        vehicle = request.POST.get("vehicle", "best")
        travel_type = request.POST.get("travel_type", "solo")
        people = request.POST.get("people", 1)
        interests = request.POST.getlist("interests")

        source_location = get_coordinates(source)
        destination_location = get_coordinates(destination)
        source_lat = source_location["latitude"] if source_location else None
        source_lon = source_location["longitude"] if source_location else None
        destination_lat = destination_location["latitude"] if destination_location else None
        destination_lon = destination_location["longitude"] if destination_location else None

        leaflet_route = []
        distance = None
        duration = None

        if source_location and destination_location:
            try:
                route_data = get_route(source_location, destination_location)
                if route_data and "features" in route_data and len(route_data["features"]) > 0:
                    feature = route_data["features"][0]
                    if "geometry" in feature:
                        coordinates = feature["geometry"]["coordinates"]
                        leaflet_route = [[p[1], p[0]] for p in coordinates]
                    if "properties" in feature and "summary" in feature["properties"]:
                        summary = feature["properties"]["summary"]
                        raw_distance = summary.get("distance")
                        raw_duration = summary.get("duration")
                        if raw_distance is not None:
                            distance = round(raw_distance / 1000, 2)
                        if raw_duration is not None:
                            duration = round(raw_duration / 3600, 2)
            except Exception as e:
                print(f"Route error: {e}")

        # Create trip in DB
        if source and destination and start_date and end_date and budget:
            from datetime import date as ddate
            try:
                sd = ddate.fromisoformat(start_date)
                ed = ddate.fromisoformat(end_date)
                num_days = (ed - sd).days + 1
                trip = Trip.objects.create(
                    user=user,
                    source=source,
                    destination=destination,
                    source_lat=source_lat,
                    source_lon=source_lon,
                    destination_lat=destination_lat,
                    destination_lon=destination_lon,
                    start_date=sd,
                    end_date=ed,
                    num_days=num_days,
                    num_travelers=int(people),
                    budget=float(budget),
                    transport=vehicle,
                    travel_type=travel_type,
                    interests=interests,
                    distance_km=distance,
                    duration_hours=duration,
                    route_coords=leaflet_route,
                    status='planning',
                )
                messages.success(request, f"Trip to {destination} created! Now generate your AI itinerary.")
                return redirect('trip_detail', trip_id=trip.id)
            except Exception as e:
                messages.error(request, f"Error creating trip: {e}")

        context.update({
            "source": source,
            "destination": destination,
            "start_date": start_date,
            "end_date": end_date,
            "budget": budget,
            "vehicle": vehicle,
            "travel_type": travel_type,
            "people": people,
            "interests": interests,
            "source_lat": source_lat,
            "source_lon": source_lon,
            "destination_lat": destination_lat,
            "destination_lon": destination_lon,
            "route": json.dumps(leaflet_route),
            "distance": distance,
            "duration": duration,
        })

    return render(request, 'User_dashboard.html', context)


# ─── Trips List ───────────────────────────────────────────────────────────────
@login_required(login_url='/login/')
def trips_page(request):
    trips = Trip.objects.filter(user=request.user).order_by('-created_at')
    status_filter = request.GET.get('status', '')
    if status_filter:
        trips = trips.filter(status=status_filter)
    return render(request, 'trips.html', {
        'trips': trips,
        'status_filter': status_filter,
        'status_choices': Trip.STATUS_CHOICES,
    })


# ─── Trip Detail ──────────────────────────────────────────────────────────────
@login_required(login_url='/login/')
def trip_detail_page(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id, user=request.user)
    itinerary = getattr(trip, 'itinerary', None)
    expenses = Expense.objects.filter(trip=trip).order_by('-date')
    budget = getattr(trip, 'budget_plan', None)
    packing = getattr(trip, 'packing_list', None)
    photos = Photo.objects.filter(trip=trip)
    journal_entries = TravelJournal.objects.filter(trip=trip)

    total_spent = sum(e.amount for e in expenses)

    return render(request, 'trip_detail.html', {
        'trip': trip,
        'itinerary': itinerary,
        'expenses': expenses,
        'budget': budget,
        'packing': packing,
        'photos': photos,
        'journal_entries': journal_entries,
        'total_spent': total_spent,
        'route': json.dumps(trip.route_coords or []),
    })


# ─── Trip Summary ─────────────────────────────────────────────────────────────
@login_required(login_url='/login/')
def trip_summary_page(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id, user=request.user)
    expenses = Expense.objects.filter(trip=trip)
    photos = Photo.objects.filter(trip=trip)
    journal = TravelJournal.objects.filter(trip=trip)
    total_spent = sum(e.amount for e in expenses)

    # Category breakdown
    by_category = {}
    for exp in expenses:
        cat = exp.get_category_display()
        by_category[cat] = float(by_category.get(cat, 0)) + float(exp.amount)

    return render(request, 'trip_summary.html', {
        'trip': trip,
        'expenses': expenses,
        'photos': photos,
        'journal': journal,
        'total_spent': total_spent,
        'by_category': json.dumps(by_category),
        'savings': float(trip.budget) - float(total_spent),
    })


# ─── AI Planner ───────────────────────────────────────────────────────────────
@login_required(login_url='/login/')
def ai_planner_page(request):
    trips = Trip.objects.filter(user=request.user).order_by('-created_at')[:10]
    return render(request, 'ai_planner.html', {'trips': trips})


# ─── Map Explorer ─────────────────────────────────────────────────────────────
@login_required(login_url='/login/')
def map_explorer_page(request):
    trips = Trip.objects.filter(user=request.user).order_by('-created_at')[:10]
    poi_types = [
        ('tourist_attraction', 'Attractions', 'landscape'),
        ('hotel', 'Hotels', 'hotel'),
        ('restaurant', 'Restaurants', 'restaurant'),
        ('cafe', 'Cafes', 'local_cafe'),
        ('hospital', 'Hospitals', 'local_hospital'),
        ('pharmacy', 'Pharmacy', 'medication'),
        ('atm', 'ATM', 'atm'),
        ('fuel', 'Fuel', 'local_gas_station'),
        ('parking', 'Parking', 'local_parking'),
        ('railway_station', 'Railway', 'train'),
        ('bus_station', 'Bus Stop', 'directions_bus'),
        ('airport', 'Airport', 'flight'),
        ('police', 'Police', 'local_police'),
        ('supermarket', 'Supermarket', 'shopping_cart'),
        ('ev_charging', 'EV Charging', 'ev_station'),
        ('toilet', 'Restrooms', 'wc'),
    ]
    return render(request, 'map_explorer.html', {'trips': trips, 'poi_types': poi_types})


# ─── Destination Explorer ─────────────────────────────────────────────────────
@login_required(login_url='/login/')
def destination_explorer_page(request):
    destinations = Destination.objects.all().order_by('-rating')
    categories = Destination.CATEGORY_CHOICES
    return render(request, 'destination_explorer.html', {
        'destinations': destinations,
        'categories': categories,
    })


# ─── Budget Planner ───────────────────────────────────────────────────────────
@login_required(login_url='/login/')
def budget_planner_page(request):
    trips = Trip.objects.filter(user=request.user).order_by('-created_at')
    selected_trip = None
    budget = None
    trip_id = request.GET.get('trip')
    if trip_id:
        selected_trip = get_object_or_404(Trip, id=trip_id, user=request.user)
        budget = getattr(selected_trip, 'budget_plan', None)

    return render(request, 'budget_planner.html', {
        'trips': trips,
        'selected_trip': selected_trip,
        'budget': budget,
    })


# ─── Expenses ─────────────────────────────────────────────────────────────────
@login_required(login_url='/login/')
def expenses_page(request):
    expenses = Expense.objects.filter(user=request.user).order_by('-date')
    trips = Trip.objects.filter(user=request.user)
    trip_id = request.GET.get('trip')
    selected_trip = None
    if trip_id:
        selected_trip = get_object_or_404(Trip, id=trip_id, user=request.user)
        expenses = expenses.filter(trip=selected_trip)

    total = sum(e.amount for e in expenses)
    by_category = {}
    for exp in expenses:
        cat = exp.category
        by_category[cat] = float(by_category.get(cat, 0)) + float(exp.amount)

    return render(request, 'expenses.html', {
        'expenses': expenses,
        'trips': trips,
        'selected_trip': selected_trip,
        'total': total,
        'by_category': json.dumps(by_category),
        'categories': Expense.CATEGORY_CHOICES,
    })


# ─── Weather ──────────────────────────────────────────────────────────────────
@login_required(login_url='/login/')
def weather_page(request):
    trips = Trip.objects.filter(user=request.user).order_by('-created_at')[:5]
    return render(request, 'weather.html', {'trips': trips})


# ─── Chatbot ──────────────────────────────────────────────────────────────────
@login_required(login_url='/login/')
def chatbot_page(request):
    history = ChatHistory.objects.filter(user=request.user).order_by('created_at')[:50]
    trips = Trip.objects.filter(user=request.user).order_by('-created_at')[:5]
    return render(request, 'chatbot.html', {'history': history, 'trips': trips})


# ─── Packing ──────────────────────────────────────────────────────────────────
@login_required(login_url='/login/')
def packing_page(request):
    trips = Trip.objects.filter(user=request.user).order_by('-created_at')
    trip_id = request.GET.get('trip')
    selected_trip = None
    packing = None
    if trip_id:
        selected_trip = get_object_or_404(Trip, id=trip_id, user=request.user)
        packing = getattr(selected_trip, 'packing_list', None)
    return render(request, 'packing.html', {
        'trips': trips,
        'selected_trip': selected_trip,
        'packing': packing,
    })


# ─── Digital Travel Wallet ────────────────────────────────────────────────────
@login_required(login_url='/login/')
def wallet_page(request):
    documents = TravelDocument.objects.filter(user=request.user).order_by('-created_at')
    emergency_contacts = EmergencyContact.objects.filter(user=request.user)
    trips = Trip.objects.filter(user=request.user).order_by('-created_at')
    doc_types = TravelDocument.DOC_TYPE_CHOICES
    return render(request, 'wallet.html', {
        'documents': documents,
        'emergency_contacts': emergency_contacts,
        'trips': trips,
        'doc_types': doc_types,
    })


# ─── Travel Journal ───────────────────────────────────────────────────────────
@login_required(login_url='/login/')
def journal_page(request):
    entries = TravelJournal.objects.filter(user=request.user).order_by('-entry_date')
    photos = Photo.objects.filter(user=request.user).order_by('-created_at')[:12]
    trips = Trip.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'journal.html', {
        'entries': entries,
        'photos': photos,
        'trips': trips,
    })


# ─── Emergency ────────────────────────────────────────────────────────────────
@login_required(login_url='/login/')
def emergency_page(request):
    contacts = EmergencyContact.objects.filter(user=request.user)
    active_trip = Trip.objects.filter(
        user=request.user, status='active'
    ).first()
    return render(request, 'emergency.html', {
        'contacts': contacts,
        'active_trip': active_trip,
    })


# ─── Profile ──────────────────────────────────────────────────────────────────
@login_required(login_url='/login/')
def profile_page(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    trips = Trip.objects.filter(user=request.user)
    total_spent = sum(
        e.amount for e in Expense.objects.filter(user=request.user)
    )

    if request.method == 'POST':
        # Update user info
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.save()

        profile.phone = request.POST.get('phone', '')
        profile.bio = request.POST.get('bio', '')
        profile.nationality = request.POST.get('nationality', '')
        if 'avatar' in request.FILES:
            profile.avatar = request.FILES['avatar']
        profile.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('profile')

    return render(request, 'profile.html', {
        'profile': profile,
        'trips': trips,
        'total_trips': trips.count(),
        'completed_trips': trips.filter(status='completed').count(),
        'total_spent': total_spent,
    })


# ─── Social / Community ───────────────────────────────────────────────────────
@login_required(login_url='/login/')
def social_page(request):
    public_trips = Trip.objects.filter(is_public=True).order_by('-created_at')[:20]
    reviews = Review.objects.filter(is_public=True, is_reported=False).order_by('-created_at')[:20]
    return render(request, 'social.html', {
        'public_trips': public_trips,
        'reviews': reviews,
    })


# ─── Admin Dashboard ──────────────────────────────────────────────────────────
@login_required(login_url='/login/')
def admin_dashboard_page(request):
    if not request.user.is_staff:
        messages.error(request, "Access denied. Admin only.")
        return redirect('user_page')

    from django.db.models import Sum, Count
    total_users = User.objects.count()
    total_trips = Trip.objects.count()
    ai_trips = Trip.objects.filter(ai_generated=True).count()
    total_reviews = Review.objects.count()
    reported_reviews = Review.objects.filter(is_reported=True).count()
    total_expenses = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0

    top_destinations = (
        Trip.objects.values('destination')
        .annotate(count=Count('id'))
        .order_by('-count')[:8]
    )
    recent_users = User.objects.order_by('-date_joined')[:10]
    recent_reviews = Review.objects.filter(is_reported=True)[:10]

    return render(request, 'admin_dashboard.html', {
        'total_users': total_users,
        'total_trips': total_trips,
        'ai_trips': ai_trips,
        'total_reviews': total_reviews,
        'reported_reviews': reported_reviews,
        'total_expenses': float(total_expenses),
        'top_destinations': list(top_destinations),
        'recent_users': recent_users,
        'recent_reviews': recent_reviews,
    })