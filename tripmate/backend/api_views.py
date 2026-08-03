import json
from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    Trip, Destination, Itinerary, Activity, Budget, Expense,
    ChatHistory, Notification, Bookmark, PackingList,
    TravelDocument, TravelJournal, EmergencyContact, Review, Photo, UserProfile
)
from .serializers import (
    RegisterSerializer, TripSerializer, TripListSerializer,
    DestinationSerializer, ItinerarySerializer, ActivitySerializer,
    BudgetSerializer, ExpenseSerializer, ChatHistorySerializer,
    NotificationSerializer, BookmarkSerializer, PackingListSerializer,
    TravelDocumentSerializer, TravelJournalSerializer,
    EmergencyContactSerializer, ReviewSerializer, PhotoSerializer,
    UserProfileSerializer
)
from .services import ai as ai_service
from .services import weather as weather_service
from .services.overpass import get_nearby_pois, get_multiple_poi_types
from .services.geocode import get_coordinates
from .services.routing import get_route


# ─── Auth API ─────────────────────────────────────────────────────────────────

class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                "message": "Account created successfully!",
                "user": {"id": user.id, "username": user.username, "email": user.email},
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        from django.contrib.auth import authenticate
        email = request.data.get('email')
        password = request.data.get('password')

        user_obj = User.objects.filter(email=email).first()
        if not user_obj:
            return Response({"error": "Email not registered."}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=user_obj.username, password=password)
        if not user:
            return Response({"error": "Invalid email or password."}, status=status.HTTP_400_BAD_REQUEST)

        refresh = RefreshToken.for_user(user)
        return Response({
            "message": "Login successful!",
            "user": {"id": user.id, "username": user.username, "email": user.email},
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }
        })


# ─── Profile API ──────────────────────────────────────────────────────────────

class ProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)

    def patch(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            # Update User model fields too
            if 'first_name' in request.data:
                request.user.first_name = request.data['first_name']
            if 'last_name' in request.data:
                request.user.last_name = request.data['last_name']
            request.user.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


# ─── Trip API ─────────────────────────────────────────────────────────────────

class TripListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return TripListSerializer
        return TripSerializer

    def get_queryset(self):
        qs = Trip.objects.filter(user=self.request.user)
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


class TripDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TripSerializer

    def get_queryset(self):
        return Trip.objects.filter(user=self.request.user)


# ─── AI Itinerary API ─────────────────────────────────────────────────────────

class GenerateItineraryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        trip_id = request.data.get('trip_id')
        try:
            trip = Trip.objects.get(id=trip_id, user=request.user)
        except Trip.DoesNotExist:
            return Response({"error": "Trip not found."}, status=404)

        trip_data = {
            'source': trip.source,
            'destination': trip.destination,
            'start_date': str(trip.start_date),
            'end_date': str(trip.end_date),
            'num_days': trip.duration_days,
            'num_travelers': trip.num_travelers,
            'budget': float(trip.budget),
            'transport': trip.transport,
            'travel_type': trip.travel_type,
            'hotel_preference': trip.hotel_preference,
            'food_preference': trip.food_preference,
            'interests': trip.interests,
        }

        result = ai_service.generate_itinerary(trip_data)
        if 'error' in result and not result.get('days'):
            return Response({"error": result['error']}, status=500)

        # Save itinerary to DB
        itinerary, created = Itinerary.objects.update_or_create(
            trip=trip,
            defaults={
                'raw_ai_response': json.dumps(result),
                'days_data': result.get('days', []),
                'total_estimated_cost': result.get('total_estimated_cost'),
                'travel_tips': result.get('travel_tips', []),
                'safety_tips': result.get('safety_tips', []),
                'eco_tips': result.get('eco_tips', []),
                'best_time_to_visit': result.get('best_time_to_visit', ''),
                'packing_list': {'essentials': result.get('packing_essentials', [])},
            }
        )

        # Save budget breakdown
        budget_data = result.get('budget_breakdown', {})
        Budget.objects.update_or_create(
            trip=trip,
            defaults={
                'total_budget': trip.budget,
                'hotel_allocation': budget_data.get('hotel', 0),
                'food_allocation': budget_data.get('food', 0),
                'transport_allocation': budget_data.get('transport', 0),
                'tickets_allocation': budget_data.get('tickets', 0),
                'shopping_allocation': budget_data.get('shopping', 0),
                'misc_allocation': budget_data.get('misc', 0),
            }
        )

        # Save activities
        Activity.objects.filter(itinerary=itinerary).delete()
        for day in result.get('days', []):
            for act in day.get('activities', []):
                Activity.objects.create(
                    itinerary=itinerary,
                    day_number=day.get('day', 1),
                    time_slot=act.get('time_slot', 'other'),
                    name=act.get('name', ''),
                    description=act.get('description', ''),
                    location=act.get('location', ''),
                    estimated_cost=act.get('estimated_cost'),
                    duration_minutes=act.get('duration_minutes'),
                    tips=act.get('tips', ''),
                )

        trip.ai_generated = True
        trip.title = result.get('title', f"{trip.source} to {trip.destination}")
        trip.save()

        return Response({
            "success": True,
            "itinerary": result,
            "trip_id": trip.id,
        })


# ─── AI Chatbot API ───────────────────────────────────────────────────────────

class ChatAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        message = request.data.get('message', '').strip()
        trip_id = request.data.get('trip_id')
        if not message:
            return Response({"error": "Message is required."}, status=400)

        # Get chat history
        history_qs = ChatHistory.objects.filter(user=request.user).order_by('-created_at')[:10]
        history = [{"role": h.role, "message": h.message} for h in reversed(history_qs)]

        # Get trip context
        trip_context = None
        if trip_id:
            try:
                trip = Trip.objects.get(id=trip_id, user=request.user)
                trip_context = {'source': trip.source, 'destination': trip.destination}
            except Trip.DoesNotExist:
                pass

        # Get AI response
        response_text = ai_service.chat_response(message, history, trip_context)

        # Save messages
        ChatHistory.objects.create(user=request.user, role='user', message=message)
        ChatHistory.objects.create(user=request.user, role='assistant', message=response_text)

        return Response({"response": response_text, "message": message})

    def get(self, request):
        """Get chat history."""
        history = ChatHistory.objects.filter(user=request.user).order_by('created_at')[:50]
        return Response({"history": ChatHistorySerializer(history, many=True).data})

    def delete(self, request):
        """Clear chat history."""
        ChatHistory.objects.filter(user=request.user).delete()
        return Response({"message": "Chat history cleared."})


# ─── Weather API ──────────────────────────────────────────────────────────────

class WeatherAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        lat = request.query_params.get('lat')
        lon = request.query_params.get('lon')
        forecast_type = request.query_params.get('type', 'current')

        if not lat or not lon:
            return Response({"error": "lat and lon parameters are required."}, status=400)

        try:
            lat, lon = float(lat), float(lon)
        except ValueError:
            return Response({"error": "Invalid lat/lon values."}, status=400)

        if forecast_type == 'hourly':
            data = weather_service.get_hourly_forecast(lat, lon)
        elif forecast_type == 'forecast':
            days = int(request.query_params.get('days', 7))
            data = weather_service.get_forecast(lat, lon, days)
        else:
            data = weather_service.get_current_weather(lat, lon)

        return Response(data)


# ─── Nearby POIs API ──────────────────────────────────────────────────────────

class NearbyAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        lat = request.query_params.get('lat')
        lon = request.query_params.get('lon')
        poi_type = request.query_params.get('type', 'tourist_attraction')
        radius = int(request.query_params.get('radius', 2000))

        if not lat or not lon:
            return Response({"error": "lat and lon required."}, status=400)

        try:
            lat, lon = float(lat), float(lon)
        except ValueError:
            return Response({"error": "Invalid coordinates."}, status=400)

        # Support multiple types
        types = poi_type.split(',')
        if len(types) > 1:
            results = get_multiple_poi_types(lat, lon, types, radius)
        else:
            results = {poi_type: get_nearby_pois(lat, lon, poi_type, radius)}

        return Response(results)


# ─── Expense API ──────────────────────────────────────────────────────────────

class ExpenseListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ExpenseSerializer

    def get_queryset(self):
        qs = Expense.objects.filter(user=self.request.user)
        trip_id = self.request.query_params.get('trip')
        if trip_id:
            qs = qs.filter(trip_id=trip_id)
        return qs

    def get_serializer_context(self):
        return {'request': self.request}


class ExpenseDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ExpenseSerializer

    def get_queryset(self):
        return Expense.objects.filter(user=self.request.user)


class ExpenseSummaryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        trip_id = request.query_params.get('trip')
        qs = Expense.objects.filter(user=request.user)
        if trip_id:
            qs = qs.filter(trip_id=trip_id)

        total = qs.aggregate(total=Sum('amount'))['total'] or 0
        by_category = qs.values('category').annotate(total=Sum('amount'), count=Count('id'))
        recent = qs.order_by('-date')[:5]

        return Response({
            "total_spent": float(total),
            "by_category": list(by_category),
            "recent": ExpenseSerializer(recent, many=True).data,
        })


# ─── Budget API ───────────────────────────────────────────────────────────────

class BudgetAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, trip_id):
        try:
            trip = Trip.objects.get(id=trip_id, user=request.user)
            budget = Budget.objects.get(trip=trip)
            return Response(BudgetSerializer(budget).data)
        except (Trip.DoesNotExist, Budget.DoesNotExist):
            return Response({"error": "Budget not found."}, status=404)

    def post(self, request, trip_id):
        try:
            trip = Trip.objects.get(id=trip_id, user=request.user)
        except Trip.DoesNotExist:
            return Response({"error": "Trip not found."}, status=404)

        data = request.data
        budget_obj = total = float(data.get('total_budget', trip.budget))

        # AI budget suggestions
        suggestions = ai_service.get_budget_suggestions(
            total, trip.destination, trip.duration_days, trip.num_travelers
        )

        budget, _ = Budget.objects.update_or_create(
            trip=trip,
            defaults={
                'total_budget': total,
                'hotel_allocation': data.get('hotel', total * 0.35),
                'food_allocation': data.get('food', total * 0.25),
                'transport_allocation': data.get('transport', total * 0.15),
                'tickets_allocation': data.get('tickets', total * 0.10),
                'shopping_allocation': data.get('shopping', total * 0.10),
                'misc_allocation': data.get('misc', total * 0.05),
                'ai_suggestions': suggestions,
            }
        )
        return Response(BudgetSerializer(budget).data)


# ─── Packing List API ─────────────────────────────────────────────────────────

class PackingListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, trip_id):
        try:
            trip = Trip.objects.get(id=trip_id, user=request.user)
            packing = PackingList.objects.get(trip=trip)
            return Response(PackingListSerializer(packing).data)
        except (Trip.DoesNotExist, PackingList.DoesNotExist):
            return Response({"error": "Packing list not found."}, status=404)

    def post(self, request, trip_id):
        """Generate AI packing list."""
        try:
            trip = Trip.objects.get(id=trip_id, user=request.user)
        except Trip.DoesNotExist:
            return Response({"error": "Trip not found."}, status=404)

        trip_data = {
            'destination': trip.destination,
            'num_days': trip.duration_days,
            'interests': trip.interests,
            'travel_type': trip.travel_type,
            'num_travelers': trip.num_travelers,
        }
        result = ai_service.generate_packing_list(trip_data)
        categories = result.get('categories', {})

        packing, _ = PackingList.objects.update_or_create(
            trip=trip,
            defaults={'items': categories, 'ai_generated': True}
        )
        return Response(PackingListSerializer(packing).data)

    def patch(self, request, trip_id):
        """Update packing list items (check/uncheck)."""
        try:
            trip = Trip.objects.get(id=trip_id, user=request.user)
            packing = PackingList.objects.get(trip=trip)
        except (Trip.DoesNotExist, PackingList.DoesNotExist):
            return Response({"error": "Packing list not found."}, status=404)

        packing.items = request.data.get('items', packing.items)
        packing.save()
        return Response(PackingListSerializer(packing).data)


# ─── Travel Documents API ─────────────────────────────────────────────────────

class TravelDocumentListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TravelDocumentSerializer

    def get_queryset(self):
        qs = TravelDocument.objects.filter(user=self.request.user)
        trip_id = self.request.query_params.get('trip')
        if trip_id:
            qs = qs.filter(trip_id=trip_id)
        return qs

    def get_serializer_context(self):
        return {'request': self.request}


class TravelDocumentDetailAPIView(generics.RetrieveDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TravelDocumentSerializer

    def get_queryset(self):
        return TravelDocument.objects.filter(user=self.request.user)


# ─── Travel Journal API ───────────────────────────────────────────────────────

class JournalListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TravelJournalSerializer

    def get_queryset(self):
        qs = TravelJournal.objects.filter(user=self.request.user)
        trip_id = self.request.query_params.get('trip')
        if trip_id:
            qs = qs.filter(trip_id=trip_id)
        return qs

    def get_serializer_context(self):
        return {'request': self.request}


class JournalDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TravelJournalSerializer

    def get_queryset(self):
        return TravelJournal.objects.filter(user=self.request.user)


# ─── Notifications API ────────────────────────────────────────────────────────

class NotificationAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def patch(self, request):
        """Mark all notifications as read."""
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"message": "All notifications marked as read."})


# ─── Bookmark API ─────────────────────────────────────────────────────────────

class BookmarkListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BookmarkSerializer

    def get_queryset(self):
        return Bookmark.objects.filter(user=self.request.user)

    def get_serializer_context(self):
        return {'request': self.request}


class BookmarkDetailAPIView(generics.RetrieveDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BookmarkSerializer

    def get_queryset(self):
        return Bookmark.objects.filter(user=self.request.user)


# ─── Emergency Contacts API ───────────────────────────────────────────────────

class EmergencyContactAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EmergencyContactSerializer

    def get_queryset(self):
        return EmergencyContact.objects.filter(user=self.request.user)

    def get_serializer_context(self):
        return {'request': self.request}


class EmergencyContactDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EmergencyContactSerializer

    def get_queryset(self):
        return EmergencyContact.objects.filter(user=self.request.user)


# ─── Review API ───────────────────────────────────────────────────────────────

class ReviewListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReviewSerializer

    def get_queryset(self):
        return Review.objects.filter(is_public=True, is_reported=False)

    def get_serializer_context(self):
        return {'request': self.request}


# ─── Photo API ────────────────────────────────────────────────────────────────

class PhotoListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PhotoSerializer

    def get_queryset(self):
        qs = Photo.objects.filter(user=self.request.user)
        trip_id = self.request.query_params.get('trip')
        if trip_id:
            qs = qs.filter(trip_id=trip_id)
        return qs

    def get_serializer_context(self):
        return {'request': self.request}


# ─── Trip Summary API ─────────────────────────────────────────────────────────

class TripSummaryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, trip_id):
        try:
            trip = Trip.objects.get(id=trip_id, user=request.user)
        except Trip.DoesNotExist:
            return Response({"error": "Trip not found."}, status=404)

        expenses = list(Expense.objects.filter(trip=trip).values('amount', 'category', 'title', 'date'))
        total_spent = sum(float(e['amount']) for e in expenses)
        places = list(Activity.objects.filter(
            itinerary__trip=trip
        ).values_list('location', flat=True).distinct())

        trip_data = {
            'source': trip.source,
            'destination': trip.destination,
            'start_date': str(trip.start_date),
            'end_date': str(trip.end_date),
            'num_days': trip.duration_days,
            'num_travelers': trip.num_travelers,
            'budget': float(trip.budget),
            'interests': trip.interests,
            'travel_type': trip.travel_type,
        }

        ai_summary = ai_service.generate_trip_summary(trip_data, expenses, places[:10])

        by_category = {}
        for exp in expenses:
            cat = exp['category']
            by_category[cat] = by_category.get(cat, 0) + float(exp['amount'])

        return Response({
            "trip": TripSerializer(trip).data,
            "ai_summary": ai_summary,
            "total_spent": total_spent,
            "budget": float(trip.budget),
            "savings": float(trip.budget) - total_spent,
            "by_category": by_category,
            "places_visited": [p for p in places if p],
            "expenses": expenses,
        })


# ─── Dashboard Stats API ──────────────────────────────────────────────────────

class DashboardStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        trips = Trip.objects.filter(user=user)
        expenses = Expense.objects.filter(user=user)
        notifications = Notification.objects.filter(user=user, is_read=False)

        upcoming = trips.filter(status='upcoming').count()
        active = trips.filter(status='active').count()
        completed = trips.filter(status='completed').count()
        total_spent = expenses.aggregate(total=Sum('amount'))['total'] or 0

        profile, _ = UserProfile.objects.get_or_create(user=user)

        return Response({
            "upcoming_trips": upcoming,
            "active_trips": active,
            "completed_trips": completed,
            "total_trips": trips.count(),
            "total_spent": float(total_spent),
            "countries_visited": profile.countries_visited,
            "travel_days": profile.total_trips,
            "unread_notifications": notifications.count(),
        })


# ─── Admin Dashboard API ──────────────────────────────────────────────────────

class AdminDashboardAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        total_users = User.objects.count()
        total_trips = Trip.objects.count()
        total_destinations = Destination.objects.count()
        total_reviews = Review.objects.count()
        reported_reviews = Review.objects.filter(is_reported=True).count()
        ai_trips = Trip.objects.filter(ai_generated=True).count()

        # Top destinations by trip count
        top_destinations = (
            Trip.objects.values('destination')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )

        # Monthly trips (last 6 months)
        from django.db.models.functions import TruncMonth
        monthly = (
            Trip.objects.annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('-month')[:6]
        )

        # Expense total
        total_tracked = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0

        return Response({
            "total_users": total_users,
            "total_trips": total_trips,
            "total_destinations": total_destinations,
            "total_reviews": total_reviews,
            "reported_reviews": reported_reviews,
            "ai_generated_trips": ai_trips,
            "total_expenses_tracked": float(total_tracked),
            "top_destinations": list(top_destinations),
            "monthly_trips": [
                {"month": m['month'].strftime('%b %Y'), "count": m['count']}
                for m in monthly if m['month']
            ],
        })


# ─── Geocode API ──────────────────────────────────────────────────────────────

class GeocodeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        place = request.query_params.get('q')
        if not place:
            return Response({"error": "Query parameter 'q' is required."}, status=400)
        coords = get_coordinates(place)
        if not coords:
            return Response({"error": "Location not found."}, status=404)
        return Response(coords)


# ─── Route API ────────────────────────────────────────────────────────────────

class RouteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        source = request.data.get('source')
        destination = request.data.get('destination')
        transport = request.data.get('transport', 'driving-car')

        if not source or not destination:
            return Response({"error": "Source and destination required."}, status=400)

        src_coords = get_coordinates(source)
        dst_coords = get_coordinates(destination)

        if not src_coords or not dst_coords:
            return Response({"error": "Could not geocode locations."}, status=400)

        route_data = get_route(src_coords, dst_coords)

        if route_data and "features" in route_data:
            feature = route_data["features"][0]
            coords = feature["geometry"]["coordinates"]
            leaflet_route = [[p[1], p[0]] for p in coords]
            summary = feature["properties"]["summary"]
            return Response({
                "source": src_coords,
                "destination": dst_coords,
                "route": leaflet_route,
                "distance_km": round(summary.get("distance", 0) / 1000, 2),
                "duration_hours": round(summary.get("duration", 0) / 3600, 2),
            })
        return Response({"error": "Route not found.", "source": src_coords, "destination": dst_coords}, status=404)


# ─── Destination Explorer API ─────────────────────────────────────────────────

class DestinationListAPIView(generics.ListAPIView):
    serializer_class = DestinationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Destination.objects.all()
        category = self.request.query_params.get('category')
        search = self.request.query_params.get('search')
        trending = self.request.query_params.get('trending')
        hidden_gem = self.request.query_params.get('hidden_gem')

        if category:
            qs = qs.filter(category=category)
        if search:
            qs = qs.filter(name__icontains=search) | qs.filter(country__icontains=search)
        if trending:
            qs = qs.filter(is_trending=True)
        if hidden_gem:
            qs = qs.filter(is_hidden_gem=True)
        return qs
