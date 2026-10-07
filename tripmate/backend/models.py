from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json


# ─── User Profile ──────────────────────────────────────────────────────────
class UserProfile(models.Model):
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female'), ('O', 'Other'), ('N', 'Prefer not to say')]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    passport_number = models.CharField(max_length=50, blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    total_trips = models.PositiveIntegerField(default=0)
    total_distance_km = models.FloatField(default=0)
    countries_visited = models.PositiveIntegerField(default=0)
    notification_email = models.BooleanField(default=True)
    notification_browser = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


# ─── Destination ────────────────────────────────────────────────────────────
class Destination(models.Model):
    CATEGORY_CHOICES = [
        ('beach', 'Beach'), ('mountain', 'Mountain'), ('city', 'City'),
        ('forest', 'Forest'), ('historical', 'Historical'), ('religious', 'Religious'),
        ('wildlife', 'Wildlife'), ('adventure', 'Adventure'), ('international', 'International'),
    ]

    name = models.CharField(max_length=200)
    country = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    image = models.ImageField(upload_to='destinations/', null=True, blank=True)
    image_url = models.URLField(blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    avg_budget_per_day = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    best_season = models.CharField(max_length=100, blank=True)
    rating = models.FloatField(default=0)
    review_count = models.PositiveIntegerField(default=0)
    is_trending = models.BooleanField(default=False)
    is_hidden_gem = models.BooleanField(default=False)
    tags = models.CharField(max_length=500, blank=True)  # comma-separated
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name}, {self.country}"

    class Meta:
        ordering = ['-rating']


# ─── Trip ────────────────────────────────────────────────────────────────────
class Trip(models.Model):
    STATUS_CHOICES = [
        ('planning', 'Planning'), ('upcoming', 'Upcoming'),
        ('active', 'Active'), ('completed', 'Completed'), ('cancelled', 'Cancelled'),
    ]
    TRANSPORT_CHOICES = [
        ('car', 'Car'), ('bike', 'Bike'), ('train', 'Train'),
        ('bus', 'Bus'), ('flight', 'Flight'), ('best', 'Best Option'),
    ]
    TRAVEL_TYPE_CHOICES = [
        ('solo', 'Solo'), ('couple', 'Couple'), ('family', 'Family'), ('friends', 'Friends'),
    ]
    HOTEL_PREF_CHOICES = [
        ('budget', 'Budget'), ('mid_range', 'Mid-Range'), ('luxury', 'Luxury'),
        ('hostel', 'Hostel'), ('airbnb', 'Airbnb'),
    ]
    FOOD_PREF_CHOICES = [
        ('vegetarian', 'Vegetarian'), ('vegan', 'Vegan'), ('non_vegetarian', 'Non-Vegetarian'),
        ('any', 'Any'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trips')
    title = models.CharField(max_length=200, blank=True)
    source = models.CharField(max_length=200)
    destination = models.CharField(max_length=200)
    source_lat = models.FloatField(null=True, blank=True)
    source_lon = models.FloatField(null=True, blank=True)
    destination_lat = models.FloatField(null=True, blank=True)
    destination_lon = models.FloatField(null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    num_days = models.PositiveIntegerField(default=1)
    num_travelers = models.PositiveIntegerField(default=1)
    budget = models.DecimalField(max_digits=12, decimal_places=2)
    transport = models.CharField(max_length=20, choices=TRANSPORT_CHOICES, default='best')
    travel_type = models.CharField(max_length=20, choices=TRAVEL_TYPE_CHOICES, default='solo')
    hotel_preference = models.CharField(max_length=20, choices=HOTEL_PREF_CHOICES, default='mid_range')
    food_preference = models.CharField(max_length=20, choices=FOOD_PREF_CHOICES, default='any')
    interests = models.JSONField(default=list)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')
    distance_km = models.FloatField(null=True, blank=True)
    duration_hours = models.FloatField(null=True, blank=True)
    route_coords = models.JSONField(default=list, blank=True)
    is_public = models.BooleanField(default=False)
    ai_generated = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='trip_covers/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}: {self.source} → {self.destination}"

    class Meta:
        ordering = ['-created_at']

    @property
    def duration_days(self):
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return self.num_days


# ─── Itinerary ──────────────────────────────────────────────────────────────
class Itinerary(models.Model):
    trip = models.OneToOneField(Trip, on_delete=models.CASCADE, related_name='itinerary')
    raw_ai_response = models.TextField(blank=True)
    days_data = models.JSONField(default=list)  # Full day-by-day data
    total_estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    packing_list = models.JSONField(default=dict)
    travel_tips = models.JSONField(default=list)
    best_time_to_visit = models.CharField(max_length=200, blank=True)
    safety_tips = models.JSONField(default=list)
    eco_tips = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Itinerary for {self.trip}"


# ─── Activity ────────────────────────────────────────────────────────────────
class Activity(models.Model):
    TIME_SLOT_CHOICES = [
        ('breakfast', 'Breakfast'), ('morning', 'Morning Activity'),
        ('lunch', 'Lunch'), ('afternoon', 'Afternoon Activity'),
        ('evening', 'Evening Activity'), ('dinner', 'Dinner'),
        ('other', 'Other'),
    ]

    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name='activities')
    day_number = models.PositiveIntegerField()
    time_slot = models.CharField(max_length=20, choices=TIME_SLOT_CHOICES)
    name = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=300, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    tips = models.TextField(blank=True)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"Day {self.day_number} - {self.time_slot}: {self.name}"

    class Meta:
        ordering = ['day_number', 'time_slot']


# ─── Budget ──────────────────────────────────────────────────────────────────
class Budget(models.Model):
    trip = models.OneToOneField(Trip, on_delete=models.CASCADE, related_name='budget_plan')
    total_budget = models.DecimalField(max_digits=12, decimal_places=2)
    hotel_allocation = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    food_allocation = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transport_allocation = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tickets_allocation = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shopping_allocation = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    misc_allocation = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ai_suggestions = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Budget for {self.trip}"

    @property
    def remaining_budget(self):
        return float(self.total_budget or 0) - float(self.total_spent or 0)

    @property
    def daily_budget(self):
        days = self.trip.duration_days
        budget = float(self.total_budget or 0)
        return budget / days if days else budget


# ─── Helper to Sync Trip Budget ──────────────────────────────────────────────
def sync_trip_budget(trip):
    if not trip:
        return None
    from decimal import Decimal
    from django.db.models import Sum

    budget_plan = getattr(trip, 'budget_plan', None)
    if not budget_plan:
        total = trip.budget or Decimal('0.00')
        budget_plan = Budget.objects.create(
            trip=trip,
            total_budget=total,
            hotel_allocation=total * Decimal('0.35'),
            food_allocation=total * Decimal('0.25'),
            transport_allocation=total * Decimal('0.15'),
            tickets_allocation=total * Decimal('0.10'),
            shopping_allocation=total * Decimal('0.10'),
            misc_allocation=total * Decimal('0.05'),
        )

    spent = trip.expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    budget_plan.total_spent = spent
    budget_plan.save(update_fields=['total_spent', 'updated_at'])
    return budget_plan


# ─── Expense ─────────────────────────────────────────────────────────────────
class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('food', 'Food'), ('hotel', 'Hotel'), ('taxi', 'Taxi'),
        ('flight', 'Flight'), ('train', 'Train'), ('fuel', 'Fuel'),
        ('shopping', 'Shopping'), ('entertainment', 'Entertainment'),
        ('medical', 'Medical'), ('misc', 'Miscellaneous'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses')
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='expenses', null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=5, default='INR')
    date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True)
    receipt = models.ImageField(upload_to='receipts/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - ₹{self.amount}"

    class Meta:
        ordering = ['-date', '-created_at']


from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=Expense)
@receiver(post_delete, sender=Expense)
def _on_expense_change_sync_budget(sender, instance, **kwargs):
    if instance.trip:
        sync_trip_budget(instance.trip)



# ─── Weather Cache ────────────────────────────────────────────────────────────
class WeatherCache(models.Model):
    latitude = models.FloatField()
    longitude = models.FloatField()
    data = models.JSONField()
    fetched_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['latitude', 'longitude']

    def __str__(self):
        return f"Weather at ({self.latitude}, {self.longitude})"


# ─── Review ──────────────────────────────────────────────────────────────────
class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='reviews', null=True, blank=True)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='reviews', null=True, blank=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    rating = models.PositiveIntegerField(default=5)  # 1-5
    likes = models.PositiveIntegerField(default=0)
    is_public = models.BooleanField(default=True)
    is_reported = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.title}"

    class Meta:
        ordering = ['-created_at']


# ─── Photo ────────────────────────────────────────────────────────────────────
class Photo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='photos')
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='photos', null=True, blank=True)
    image = models.ImageField(upload_to='travel_photos/')
    caption = models.CharField(max_length=300, blank=True)
    location = models.CharField(max_length=200, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    taken_at = models.DateTimeField(null=True, blank=True)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo by {self.user.username}: {self.caption or 'No caption'}"

    class Meta:
        ordering = ['-created_at']


# ─── Travel Document ──────────────────────────────────────────────────────────
class TravelDocument(models.Model):
    DOC_TYPE_CHOICES = [
        ('passport', 'Passport'), ('visa', 'Visa'), ('driving_license', 'Driving License'),
        ('id_card', 'ID Card / Aadhaar'), ('insurance', 'Travel Insurance'),
        ('flight_ticket', 'Flight Ticket'), ('train_ticket', 'Train Ticket'),
        ('hotel_booking', 'Hotel Booking'), ('other', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='documents', null=True, blank=True)
    doc_type = models.CharField(max_length=30, choices=DOC_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='travel_docs/')
    expiry_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.doc_type} - {self.title}"

    class Meta:
        ordering = ['-created_at']


# ─── Notification ─────────────────────────────────────────────────────────────
class Notification(models.Model):
    TYPE_CHOICES = [
        ('trip_reminder', 'Trip Reminder'), ('flight', 'Flight Alert'),
        ('hotel_checkin', 'Hotel Check-in'), ('packing', 'Packing Reminder'),
        ('weather', 'Weather Alert'), ('budget', 'Budget Alert'),
        ('activity', 'Activity Reminder'), ('system', 'System'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, null=True, blank=True)
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.title}"

    class Meta:
        ordering = ['-created_at']


# ─── Chat History ─────────────────────────────────────────────────────────────
class ChatHistory(models.Model):
    ROLE_CHOICES = [('user', 'User'), ('assistant', 'Assistant')]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_history')
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, null=True, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} [{self.role}]: {self.message[:50]}"

    class Meta:
        ordering = ['created_at']


# ─── Bookmark ─────────────────────────────────────────────────────────────────
class Bookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} saved: {self.name}"

    class Meta:
        ordering = ['-created_at']


# ─── Packing List ─────────────────────────────────────────────────────────────
class PackingList(models.Model):
    trip = models.OneToOneField(Trip, on_delete=models.CASCADE, related_name='packing_list')
    items = models.JSONField(default=dict)  # {category: [{name, checked, essential}]}
    ai_generated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Packing list for {self.trip}"


# ─── Travel Journal ───────────────────────────────────────────────────────────
class TravelJournal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='journal_entries')
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='journal_entries', null=True, blank=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    mood = models.CharField(max_length=50, blank=True)
    location = models.CharField(max_length=200, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    entry_date = models.DateField(default=timezone.now)
    ai_generated_summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}: {self.title}"

    class Meta:
        ordering = ['-entry_date']


# ─── Emergency Contact ────────────────────────────────────────────────────────
class EmergencyContact(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emergency_contacts')
    name = models.CharField(max_length=200)
    relationship = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.relationship}) - {self.user.username}"

    class Meta:
        ordering = ['-is_primary', 'name']


# ─── Community Post ───────────────────────────────────────────────────────────
class CommunityPost(models.Model):
    POST_TYPE_CHOICES = [
        ('text', 'Text'), ('photo', 'Photo'),
        ('experience', 'Experience'), ('review', 'Review'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='community_posts')
    content = models.TextField()
    image = models.ImageField(upload_to='community_posts/', null=True, blank=True)
    post_type = models.CharField(max_length=20, choices=POST_TYPE_CHOICES, default='text')
    location = models.CharField(max_length=200, blank=True)
    likes_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}: {self.content[:50]}"

    class Meta:
        ordering = ['-created_at']


# ─── Post Like ────────────────────────────────────────────────────────────────
class PostLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_likes')
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'post']

    def __str__(self):
        return f"{self.user.username} liked post #{self.post.id}"


# ─── Post Comment ─────────────────────────────────────────────────────────────
class PostComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_comments')
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} on post #{self.post.id}: {self.content[:40]}"

    class Meta:
        ordering = ['created_at']


# ─── Direct Message ───────────────────────────────────────────────────────────
class DirectMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username} → {self.receiver.username}: {self.content[:40]}"

    class Meta:
        ordering = ['created_at']