from django.contrib import admin
from .models import (
    UserProfile, Trip, Destination, Itinerary, Activity,
    Budget, Expense, WeatherCache, Review, Photo,
    TravelDocument, Notification, ChatHistory, Bookmark,
    PackingList, TravelJournal, EmergencyContact
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'nationality', 'total_trips', 'countries_visited', 'created_at']
    search_fields = ['user__username', 'user__email', 'nationality']


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ['user', 'source', 'destination', 'start_date', 'end_date', 'status', 'ai_generated']
    list_filter = ['status', 'transport', 'travel_type', 'ai_generated']
    search_fields = ['user__username', 'source', 'destination']
    date_hierarchy = 'start_date'


@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ['name', 'country', 'category', 'rating', 'is_trending', 'is_hidden_gem']
    list_filter = ['category', 'is_trending', 'is_hidden_gem']
    search_fields = ['name', 'country']


@admin.register(Itinerary)
class ItineraryAdmin(admin.ModelAdmin):
    list_display = ['trip', 'total_estimated_cost', 'created_at']


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ['itinerary', 'day_number', 'time_slot', 'name', 'estimated_cost']
    list_filter = ['time_slot', 'is_completed']


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ['trip', 'total_budget', 'total_spent', 'created_at']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'category', 'amount', 'date']
    list_filter = ['category']
    search_fields = ['user__username', 'title']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'rating', 'is_public', 'is_reported', 'created_at']
    list_filter = ['is_reported', 'is_public', 'rating']
    actions = ['approve_reviews', 'mark_reported']

    def approve_reviews(self, request, queryset):
        queryset.update(is_reported=False, is_public=True)
    approve_reviews.short_description = "Approve selected reviews"

    def mark_reported(self, request, queryset):
        queryset.update(is_reported=True)
    mark_reported.short_description = "Mark as reported"


@admin.register(TravelDocument)
class TravelDocumentAdmin(admin.ModelAdmin):
    list_display = ['user', 'doc_type', 'title', 'expiry_date', 'created_at']
    list_filter = ['doc_type']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read']


@admin.register(ChatHistory)
class ChatHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'message', 'created_at']
    list_filter = ['role']


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'created_at']


@admin.register(PackingList)
class PackingListAdmin(admin.ModelAdmin):
    list_display = ['trip', 'ai_generated', 'created_at']


@admin.register(TravelJournal)
class TravelJournalAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'entry_date', 'created_at']
    search_fields = ['user__username', 'title']


@admin.register(EmergencyContact)
class EmergencyContactAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'relationship', 'phone', 'is_primary']


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ['user', 'caption', 'location', 'is_public', 'created_at']
    list_filter = ['is_public']


@admin.register(WeatherCache)
class WeatherCacheAdmin(admin.ModelAdmin):
    list_display = ['latitude', 'longitude', 'fetched_at']
