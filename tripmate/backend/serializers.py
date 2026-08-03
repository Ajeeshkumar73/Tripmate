from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    UserProfile, Trip, Destination, Itinerary, Activity,
    Budget, Expense, WeatherCache, Review, Photo,
    TravelDocument, Notification, ChatHistory, Bookmark,
    PackingList, TravelJournal, EmergencyContact
)


# ─── User & Auth ─────────────────────────────────────────────────────────────
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirm_password', 'first_name', 'last_name']

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("Email already registered.")
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(**validated_data)
        UserProfile.objects.create(user=user)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'full_name', 'avatar', 'phone', 'bio',
                  'nationality', 'date_of_birth', 'gender', 'total_trips',
                  'total_distance_km', 'countries_visited', 'notification_email',
                  'notification_browser', 'created_at']

    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username


# ─── Destination ─────────────────────────────────────────────────────────────
class DestinationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = '__all__'


# ─── Trip ─────────────────────────────────────────────────────────────────────
class TripSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    duration_days = serializers.ReadOnlyField()
    has_itinerary = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']

    def get_has_itinerary(self, obj):
        return hasattr(obj, 'itinerary')

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class TripListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for trip lists."""
    duration_days = serializers.ReadOnlyField()
    has_itinerary = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = ['id', 'title', 'source', 'destination', 'start_date', 'end_date',
                  'duration_days', 'budget', 'status', 'transport', 'travel_type',
                  'num_travelers', 'has_itinerary', 'ai_generated', 'cover_image',
                  'created_at']

    def get_has_itinerary(self, obj):
        return hasattr(obj, 'itinerary')


# ─── Activity ─────────────────────────────────────────────────────────────────
class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = '__all__'


# ─── Itinerary ────────────────────────────────────────────────────────────────
class ItinerarySerializer(serializers.ModelSerializer):
    activities = ActivitySerializer(many=True, read_only=True)

    class Meta:
        model = Itinerary
        fields = '__all__'


# ─── Budget ───────────────────────────────────────────────────────────────────
class BudgetSerializer(serializers.ModelSerializer):
    remaining_budget = serializers.ReadOnlyField()
    daily_budget = serializers.ReadOnlyField()

    class Meta:
        model = Budget
        fields = '__all__'


# ─── Expense ──────────────────────────────────────────────────────────────────
class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = '__all__'
        read_only_fields = ['user', 'created_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


# ─── Review ───────────────────────────────────────────────────────────────────
class ReviewSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Review
        fields = '__all__'
        read_only_fields = ['user', 'likes', 'created_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


# ─── Photo ────────────────────────────────────────────────────────────────────
class PhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = '__all__'
        read_only_fields = ['user', 'created_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


# ─── Travel Document ──────────────────────────────────────────────────────────
class TravelDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TravelDocument
        fields = '__all__'
        read_only_fields = ['user', 'created_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


# ─── Notification ─────────────────────────────────────────────────────────────
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'


# ─── Chat History ─────────────────────────────────────────────────────────────
class ChatHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatHistory
        fields = '__all__'


# ─── Bookmark ─────────────────────────────────────────────────────────────────
class BookmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bookmark
        fields = '__all__'
        read_only_fields = ['user', 'created_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


# ─── Packing List ─────────────────────────────────────────────────────────────
class PackingListSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackingList
        fields = '__all__'


# ─── Travel Journal ───────────────────────────────────────────────────────────
class TravelJournalSerializer(serializers.ModelSerializer):
    class Meta:
        model = TravelJournal
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


# ─── Emergency Contact ────────────────────────────────────────────────────────
class EmergencyContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyContact
        fields = '__all__'
        read_only_fields = ['user', 'created_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
