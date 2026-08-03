import os
import json
from groq import Groq
from django.conf import settings

client = Groq(api_key=settings.GROQ_API_KEY)

SYSTEM_PROMPT = """You are TripMate AI, an expert travel planning assistant. 
You help users plan amazing trips with detailed, practical, and personalized recommendations.
Always respond in valid JSON format when asked to generate structured data.
Be concise, helpful, and enthusiastic about travel."""


def generate_itinerary(trip_data: dict) -> dict:
    """Generate a day-wise itinerary using Groq AI."""
    prompt = f"""Create a detailed day-by-day travel itinerary for the following trip:

Source: {trip_data.get('source')}
Destination: {trip_data.get('destination')}
Start Date: {trip_data.get('start_date')}
End Date: {trip_data.get('end_date')}
Number of Days: {trip_data.get('num_days', 1)}
Number of Travelers: {trip_data.get('num_travelers', 1)}
Budget: ₹{trip_data.get('budget')}
Transport: {trip_data.get('transport', 'best option')}
Travel Type: {trip_data.get('travel_type', 'solo')}
Hotel Preference: {trip_data.get('hotel_preference', 'mid_range')}
Food Preference: {trip_data.get('food_preference', 'any')}
Interests: {', '.join(trip_data.get('interests', []))}

Return a JSON object with this exact structure:
{{
  "title": "Trip title",
  "overview": "Brief overview of the trip",
  "days": [
    {{
      "day": 1,
      "date": "YYYY-MM-DD",
      "theme": "Day theme",
      "weather_note": "Expected weather",
      "estimated_cost": 2000,
      "activities": [
        {{
          "time_slot": "breakfast",
          "name": "Activity/Place name",
          "description": "Details",
          "location": "Place name",
          "estimated_cost": 300,
          "duration_minutes": 45,
          "tips": "Helpful tip"
        }},
        {{"time_slot": "morning", ...}},
        {{"time_slot": "lunch", ...}},
        {{"time_slot": "afternoon", ...}},
        {{"time_slot": "evening", ...}},
        {{"time_slot": "dinner", ...}}
      ]
    }}
  ],
  "hotels": [
    {{"name": "Hotel name", "area": "Area", "price_per_night": 1500, "rating": 4.2, "amenities": ["wifi", "pool"]}}
  ],
  "total_estimated_cost": 15000,
  "budget_breakdown": {{
    "hotel": 5000,
    "food": 3000,
    "transport": 2000,
    "tickets": 2000,
    "shopping": 1500,
    "misc": 1500
  }},
  "travel_tips": ["Tip 1", "Tip 2", "Tip 3"],
  "safety_tips": ["Safety tip 1", "Safety tip 2"],
  "best_time_to_visit": "October to March",
  "eco_tips": ["Eco-friendly tip 1", "Eco-friendly tip 2"],
  "packing_essentials": ["Item 1", "Item 2"]
}}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4096,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        return {"error": str(e), "days": [], "overview": "Failed to generate itinerary. Please try again."}


def chat_response(message: str, history: list, trip_context: dict = None) -> str:
    """Get AI chatbot response for travel queries."""
    context = ""
    if trip_context:
        context = f"\nCurrent trip context: {trip_context.get('source')} to {trip_context.get('destination')}"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + context},
    ]
    # Add history (last 10 messages)
    for msg in history[-10:]:
        messages.append({"role": msg["role"], "content": msg["message"]})
    messages.append({"role": "user", "content": message})

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.8,
            max_tokens=1024,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"I'm having trouble connecting right now. Please try again. (Error: {str(e)})"


def generate_packing_list(trip_data: dict) -> dict:
    """Generate a smart packing list based on trip details."""
    prompt = f"""Generate a comprehensive packing checklist for this trip:

Destination: {trip_data.get('destination')}
Duration: {trip_data.get('num_days', 1)} days
Season/Weather: {trip_data.get('weather_note', 'Unknown')}
Activities: {', '.join(trip_data.get('interests', []))}
Travel Type: {trip_data.get('travel_type', 'solo')}
Number of Travelers: {trip_data.get('num_travelers', 1)}

Return JSON with this structure:
{{
  "categories": {{
    "Clothes": [
      {{"name": "T-shirts (5)", "essential": true, "checked": false}},
      ...
    ],
    "Electronics": [...],
    "Documents": [...],
    "Medicines": [...],
    "Toiletries": [...],
    "Accessories": [...]
  }}
}}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            max_tokens=2048,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"error": str(e), "categories": {}}


def generate_trip_summary(trip_data: dict, expenses: list, places_visited: list) -> str:
    """Generate an AI travel diary/summary after trip completion."""
    prompt = f"""Write a beautiful, engaging travel diary summary for this completed trip:

Trip: {trip_data.get('source')} to {trip_data.get('destination')}
Dates: {trip_data.get('start_date')} to {trip_data.get('end_date')}
Duration: {trip_data.get('num_days')} days
Travelers: {trip_data.get('num_travelers')} ({trip_data.get('travel_type')})
Total Budget: ₹{trip_data.get('budget')}
Total Spent: ₹{sum(e.get('amount', 0) for e in expenses)}
Places Visited: {', '.join(places_visited) if places_visited else 'Various places'}
Interests: {', '.join(trip_data.get('interests', []))}

Write a warm, personal, narrative-style travel diary entry (300-400 words) that captures the essence of the journey."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a gifted travel writer who creates beautiful, personal travel narratives."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.9,
            max_tokens=1024,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Unable to generate travel summary at this time."


def suggest_alternative_itinerary(trip_data: dict, weather_alert: str) -> dict:
    """Suggest alternative activities when weather is bad."""
    prompt = f"""The weather forecast shows: {weather_alert}

Suggest 5 indoor/weather-appropriate alternative activities for:
Destination: {trip_data.get('destination')}
Interests: {', '.join(trip_data.get('interests', []))}

Return JSON:
{{
  "alternatives": [
    {{"name": "Activity name", "description": "Brief description", "estimated_cost": 500, "duration": "2-3 hours"}},
    ...
  ],
  "general_advice": "Brief weather travel advice"
}}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1024,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"alternatives": [], "general_advice": "Please check local conditions before heading out."}


def get_budget_suggestions(budget: float, destination: str, days: int, travelers: int) -> list:
    """Get AI-powered budget saving tips."""
    prompt = f"""Provide 6 specific money-saving tips for a trip to {destination} for {days} days with {travelers} travelers and a budget of ₹{budget}.
Return JSON: {{"suggestions": ["tip1", "tip2", ...]}}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=512,
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        return data.get("suggestions", [])
    except Exception:
        return ["Book accommodation in advance", "Use public transport", "Eat at local restaurants"]
