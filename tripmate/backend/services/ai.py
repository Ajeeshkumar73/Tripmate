import os
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Primary & Fallback Groq models
GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "mixtral-8x7b-32768",
]

SYSTEM_PROMPT = """You are TripMate Assistant, a friendly and expert travel guide. Your job is to give clear, well-organized, clean, and easy-to-understand answers — even a person who has never traveled before should fully understand your response.

STRICT FORMATTING & STYLE RULES (always follow these):
1. DO NOT use any emojis anywhere in your response (no emojis at all). Keep the text completely clean, plain, and professional.
2. ALWAYS start with a one-sentence direct answer to the question.
3. Use clear section headings ending with a colon (e.g. "Top Places to Visit:", "Budget Tips:", "What You Need:").
4. Under each heading, use bullet points (•) with short, simple sentences. One idea per bullet. Max 2 lines per bullet.
5. Use everyday simple English. Avoid travel jargon or technical words. If you must use one, explain it in brackets.
6. End every response with a short "Quick Tip:" that gives one most important piece of advice.
7. Keep total response under 350 words. Be specific, not vague.
8. Never use markdown formatting like **, ##, or ---. Use plain text with the heading format shown above.
9. If a question has multiple parts, answer each part in its own clearly labeled section.
10. Numbers, costs, and durations make answers much more useful — always include them when possible.

EXAMPLE FORMAT:
[One clear, direct answer sentence.]

Best Places to Visit:
• Red Fort, Delhi — India's most iconic historical monument. Entry ₹35 for Indians.
• Marine Drive, Mumbai — A beautiful 3.6 km seafront road. Free to walk anytime.

Budget Estimate:
• Food: ₹300–600 per day at local restaurants
• Hotel: ₹800–2000 per night for a decent stay

Quick Tip: Book train tickets at least 2 weeks in advance to get the best prices on IRCTC."""


def get_groq_client():
    api_key = os.getenv('GROQ_API_KEY', '') or os.getenv('GROQ_API', '') or getattr(settings, 'GROQ_API_KEY', '')
    if not api_key:
        return None
    try:
        from groq import Groq
        return Groq(api_key=api_key)
    except Exception as e:
        logger.error(f"Failed to initialize Groq client: {e}")
        return None


def _call_groq(messages: list, temperature: float = 0.7, max_tokens: int = 2048, json_mode: bool = False):
    client = get_groq_client()
    if not client:
        return None

    for model_name in GROQ_MODELS:
        try:
            kwargs = {
                "model": model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}

            response = client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content
            if content:
                if json_mode:
                    clean_content = content.strip()
                    if clean_content.startswith("```json"):
                        clean_content = clean_content[7:]
                    if clean_content.startswith("```"):
                        clean_content = clean_content[3:]
                    if clean_content.endswith("```"):
                        clean_content = clean_content[:-3]
                    clean_content = clean_content.strip()
                    return json.loads(clean_content)
                return content
        except Exception as e:
            logger.warning(f"Groq API model {model_name} failed: {e}")
            continue

    return None


def generate_fallback_itinerary(trip_data: dict) -> dict:
    """Generate structured fallback day-by-day itinerary when AI endpoint is unreachable."""
    source = trip_data.get('source', 'Origin')
    dest = trip_data.get('destination', 'Destination')
    num_days = max(1, int(trip_data.get('num_days', 3)))
    budget = float(trip_data.get('budget', 15000))
    travel_type = trip_data.get('travel_type', 'solo')
    interests = trip_data.get('interests', [])
    interests_str = ', '.join(interests) if interests else 'Local exploration & sightseeing'

    daily_budget = round(budget / num_days, 2)
    days = []

    primary_interest = interests[0] if interests else 'City'

    day_themes = [
        ("Arrival & City Orientation", "Settle in, explore the main square and nearby streets."),
        ("Historic Landmarks & Heritage", "Visit historic monuments, forts, and UNESCO sites."),
        ("Nature & Adventure", "Explore parks, lakes, hikes, or scenic viewpoints."),
        ("Markets, Arts & Culture", "Explore local bazaars, craft stores, and art galleries."),
        ("Food, Festivals & Local Life", "Deep dive into local cuisine, festivals, and neighborhood walks."),
        ("Day Trip & Surrounding Area", "Explore a nearby village, waterfall, or scenic area."),
        ("Leisure, Spa & Departure Prep", "Relax, last-minute shopping, and prepare for departure."),
    ]

    morning_options = [
        (f"Explore {dest} Old Town", f"Wander through historic alleys and heritage landmarks.", f"Old Town, {dest}"),
        (f"{dest} Fort & Palace Tour", f"Visit iconic forts, palaces or historical monuments.", f"Central {dest}"),
        (f"Scenic Garden & Lake Walk", f"Enjoy morning walks in botanical gardens or lakeside promenade.", f"Lake Area, {dest}"),
        (f"Wildlife & Nature Reserve", f"Explore sanctuaries and wildlife habitats near {dest}.", f"Outskirts, {dest}"),
        (f"Heritage Museum Visit", f"Discover history, art, and cultural exhibits.", f"Museum District, {dest}"),
        (f"Sunrise Viewpoint Trek", f"Early morning hike to catch the spectacular sunrise panorama.", f"Hills near {dest}"),
        (f"Local Market & Craft Walk", f"Browse vibrant local handicraft and spice markets.", f"Market Area, {dest}"),
    ]

    afternoon_options = [
        (f"Street Food & Local Cuisine Tour", f"Sample signature street foods and local delicacies.", f"Food Street, {dest}"),
        (f"Temples & Spiritual Sites", f"Visit iconic temples, shrines, and spiritual landmarks.", f"Temple Complex, {dest}"),
        (f"Adventure Activity – {primary_interest}", f"Enjoy adventure activities like {interests_str}.", f"Activity Hub, {dest}"),
        (f"Local Shopping & Souvenirs", f"Pick up handmade crafts, textiles, and souvenirs.", f"Souvenir Street, {dest}"),
        (f"Cooking Class & Food Experience", f"Learn to cook regional specialties with a local chef.", f"Cooking Studio, {dest}"),
        (f"Cycling Tour Around {dest}", f"Scenic cycling route through culturally rich neighborhoods.", f"City Cycle Route, {dest}"),
        (f"River Cruise or Boat Ride", f"Relaxing river or lake cruise with scenic views.", f"Waterfront, {dest}"),
    ]

    evening_options = [
        (f"Sunset at {dest} Viewpoint", f"Watch golden sunset from the most scenic spot in {dest}.", f"Hilltop Viewpoint, {dest}"),
        (f"Cultural Show & Performance", f"Enjoy classical dance, music, or folk performances.", f"Cultural Center, {dest}"),
        (f"Night Market & Street Stalls", f"Explore vibrant night markets and food stalls.", f"Night Market, {dest}"),
        (f"Beachside or Lakeside Evening", f"Relax by the water and enjoy the evening breeze.", f"Waterfront, {dest}"),
        (f"Rooftop Dinner & City Lights", f"Enjoy panoramic city views from a rooftop restaurant.", f"Rooftop, {dest}"),
        (f"Traditional Evening Walk", f"Stroll through illuminated heritage streets and galis.", f"Heritage Walk, {dest}"),
        (f"Star Gazing & Bonfire", f"Enjoy clear skies and stargazing at outskirts.", f"Outskirts, {dest}"),
    ]

    for d in range(1, num_days + 1):
        theme_idx = (d - 1) % len(day_themes)
        theme_name, theme_desc = day_themes[theme_idx]
        morning = morning_options[(d - 1) % len(morning_options)]
        afternoon = afternoon_options[(d - 1) % len(afternoon_options)]
        evening = evening_options[(d - 1) % len(evening_options)]

        day_activities = [
            {
                "time_slot": "breakfast",
                "name": f"Day {d}: Morning Breakfast",
                "description": f"Start Day {d} with authentic local breakfast and coffee in {dest}.",
                "location": f"Cafe District, {dest}",
                "estimated_cost": round(daily_budget * 0.08),
                "duration_minutes": 45,
                "tips": "Try the local specialty breakfast dish."
            },
            {
                "time_slot": "morning",
                "name": f"Day {d}: {morning[0]}",
                "description": morning[1],
                "location": morning[2],
                "estimated_cost": round(daily_budget * 0.22),
                "duration_minutes": 180,
                "tips": "Start early to avoid crowds."
            },
            {
                "time_slot": "lunch",
                "name": f"Day {d}: Local Lunch",
                "description": f"Enjoy a hearty regional lunch with local specialties in {dest}.",
                "location": f"Local Restaurant, {dest}",
                "estimated_cost": round(daily_budget * 0.12),
                "duration_minutes": 60,
                "tips": "Ask the waiter for today's chef special."
            },
            {
                "time_slot": "afternoon",
                "name": f"Day {d}: {afternoon[0]}",
                "description": afternoon[1],
                "location": afternoon[2],
                "estimated_cost": round(daily_budget * 0.25),
                "duration_minutes": 150,
                "tips": "Carry water and comfortable walking shoes."
            },
            {
                "time_slot": "evening",
                "name": f"Day {d}: {evening[0]}",
                "description": evening[1],
                "location": evening[2],
                "estimated_cost": round(daily_budget * 0.13),
                "duration_minutes": 90,
                "tips": "Perfect time for photography."
            },
            {
                "time_slot": "dinner",
                "name": f"Day {d}: Dinner Experience",
                "description": f"End Day {d} with a memorable dinner, exploring the evening ambiance of {dest}.",
                "location": f"Dinner District, {dest}",
                "estimated_cost": round(daily_budget * 0.2),
                "duration_minutes": 90,
                "tips": "Reservation recommended at popular restaurants."
            },
        ]

        days.append({
            "day": d,
            "date": trip_data.get('start_date', ''),
            "theme": f"Day {d}: {theme_name}",
            "weather_note": "Pleasant and clear",
            "estimated_cost": daily_budget,
            "activities": day_activities
        })


    hotel_alloc = round(budget * 0.35, 2)
    food_alloc = round(budget * 0.25, 2)
    transport_alloc = round(budget * 0.15, 2)
    tickets_alloc = round(budget * 0.10, 2)
    shopping_alloc = round(budget * 0.10, 2)
    misc_alloc = round(budget * 0.05, 2)

    return {
        "title": f"Explore {dest} - {num_days} Days Itinerary",
        "overview": f"A personalized {num_days}-day journey from {source} to {dest} tailored for {travel_type} travel with budget ₹{budget:,.0f}.",
        "days": days,
        "hotels": [
            {"name": f"Grand Stay {dest}", "area": "City Center", "price_per_night": round(hotel_alloc / max(1, num_days)), "rating": 4.5, "amenities": ["Wi-Fi", "Breakfast Included", "AC"]}
        ],
        "total_estimated_cost": budget,
        "budget_breakdown": {
            "hotel": hotel_alloc,
            "food": food_alloc,
            "transport": transport_alloc,
            "tickets": tickets_alloc,
            "shopping": shopping_alloc,
            "misc": misc_alloc
        },
        "travel_tips": [
            "Keep digital & physical copies of your travel IDs.",
            f"Download offline map navigation for {dest}.",
            "Maintain emergency contact numbers handy."
        ],
        "safety_tips": [
            "Stay in well-lit areas during late hours.",
            "Keep your valuables secure while traveling."
        ],
        "best_time_to_visit": "October to March",
        "eco_tips": [
            "Carry a reusable water bottle to reduce plastic waste.",
            "Use public transport or walk for short distances."
        ],
        "packing_essentials": ["Comfortable walking shoes", "Sunscreen & Sunglasses", "Power bank", "Personal Medication"]
    }


def generate_itinerary(trip_data: dict) -> dict:
    """Generate a day-wise itinerary using Groq AI with automatic fallback."""
    prompt = f"""Create a detailed day-by-day travel itinerary for:
Source: {trip_data.get('source')}
Destination: {trip_data.get('destination')}
Start Date: {trip_data.get('start_date')}
End Date: {trip_data.get('end_date')}
Number of Days: {trip_data.get('num_days', 1)}
Number of Travelers: {trip_data.get('num_travelers', 1)}
Budget: ₹{trip_data.get('budget')}
Transport: {trip_data.get('transport', 'best option')}
Travel Type: {trip_data.get('travel_type', 'solo')}
Interests: {', '.join(trip_data.get('interests', []))}

Return JSON object:
{{
  "title": "Trip title",
  "overview": "Brief overview",
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
          "name": "Activity name",
          "description": "Details",
          "location": "Place name",
          "estimated_cost": 300,
          "duration_minutes": 45,
          "tips": "Tip"
        }}
      ]
    }}
  ],
  "total_estimated_cost": 15000,
  "budget_breakdown": {{"hotel": 5000, "food": 3000, "transport": 2000, "tickets": 2000, "shopping": 1500, "misc": 1500}},
  "travel_tips": ["Tip 1", "Tip 2"],
  "safety_tips": ["Safety 1"],
  "best_time_to_visit": "Best season",
  "eco_tips": ["Eco tip"],
  "packing_essentials": ["Item 1"]
}}"""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ]

    # Use more tokens for longer trips; each day needs ~800-1000 tokens
    num_days = int(trip_data.get('num_days', 3))
    token_budget = max(4000, min(8000, num_days * 1100))
    result = _call_groq(messages, temperature=0.7, max_tokens=token_budget, json_mode=True)
    if result and isinstance(result, dict) and result.get('days'):
        # If AI returned fewer days than requested, fill remaining with fallback
        returned_days = len(result['days'])
        if returned_days < num_days:
            logger.warning(f"AI returned {returned_days} days, expected {num_days}. Filling remaining with fallback.")
            fallback = generate_fallback_itinerary(trip_data)
            existing_day_nums = {d['day'] for d in result['days']}
            for fb_day in fallback['days']:
                if fb_day['day'] not in existing_day_nums:
                    result['days'].append(fb_day)
            result['days'].sort(key=lambda x: x['day'])
        return result

    logger.warning("Groq AI response incomplete or failed, using smart fallback itinerary.")
    return generate_fallback_itinerary(trip_data)


def chat_response(message: str, history: list, trip_context: dict = None) -> str:
    """Get AI chatbot response for travel queries with fallbacks."""
    context = ""
    if trip_context:
        context = f"\nCurrent trip context: {trip_context.get('source')} to {trip_context.get('destination')}"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + context},
    ]
    for msg in history[-10:]:
        messages.append({"role": msg["role"], "content": msg["message"]})
    messages.append({"role": "user", "content": message})

    ai_reply = _call_groq(messages, temperature=0.8, max_tokens=1024, json_mode=False)
    if ai_reply and ai_reply.strip():
        return ai_reply.strip()

    # Fallback response if API models fail
    dest = trip_context.get('destination', 'your destination') if trip_context else 'your destination'
    msg_lower = message.lower()

    if 'place' in msg_lower or 'visit' in msg_lower or 'attraction' in msg_lower or 'see' in msg_lower:
        return f"Top recommended places to visit in {dest}:\n\n1. Historic City Center & Heritage Monuments\n2. Scenic Viewpoints & Natural Landmarks\n3. Cultural Night Markets & Local Bazaars\n4. Museums & Local Art Galleries\n5. Famous Food Streets & Local Eateries"
    elif 'pack' in msg_lower or 'cloth' in msg_lower or 'bag' in msg_lower:
        return f"Packing Essentials for {dest}:\n\n• Comfortable walking shoes & versatile clothing\n• Passports, IDs & digital copies of bookings\n• Universal travel adapter & high-capacity power bank\n• Sunscreen, personal medication & toiletries\n• Weather-appropriate outerwear"
    elif 'hotel' in msg_lower or 'stay' in msg_lower or 'food' in msg_lower or 'restaurant' in msg_lower:
        return f"Stay & Food Recommendations in {dest}:\n\n• Choose stays near city transit hubs for easy access.\n• Try top-rated regional bistros and food markets.\n• Boutique homestays and heritage hotels offer authentic local experiences."
    elif 'visa' in msg_lower or 'doc' in msg_lower:
        return "Visa & Travel Guidance:\n\n• Ensure passport is valid for at least 6 months.\n• Check e-Visa or Visa on Arrival eligibility for your destination.\n• Keep travel insurance and return flight confirmations handy."
    else:
        return f"I'm TripMate Assistant! I can help you plan itinerary details, find attractions, suggest packing lists, or estimate travel budgets for {dest}. How can I assist your journey today?"


def generate_packing_list(trip_data: dict) -> dict:
    """Generate a smart packing list based on trip details."""
    prompt = f"""Generate a comprehensive packing checklist for:
Destination: {trip_data.get('destination')}
Duration: {trip_data.get('num_days', 1)} days
Interests: {', '.join(trip_data.get('interests', []))}
Travel Type: {trip_data.get('travel_type', 'solo')}

Return JSON:
{{
  "categories": {{
    "Clothes": [{{"name": "T-shirts (5)", "essential": true, "checked": false}}],
    "Electronics": [{{"name": "Phone Charger", "essential": true, "checked": false}}],
    "Documents": [{{"name": "ID Proof", "essential": true, "checked": false}}],
    "Medicines": [{{"name": "First Aid Kit", "essential": true, "checked": false}}],
    "Toiletries": [{{"name": "Toothbrush", "essential": true, "checked": false}}]
  }}
}}"""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ]

    result = _call_groq(messages, temperature=0.6, max_tokens=1500, json_mode=True)
    if result and isinstance(result, dict) and result.get('categories'):
        return result

    dest = trip_data.get('destination', 'Trip')
    return {
        "categories": {
            "Clothes": [
                {"name": f"Light clothes for {dest}", "essential": True, "checked": False},
                {"name": "Comfortable Walking Shoes", "essential": True, "checked": False},
                {"name": "Jacket / Sweater", "essential": False, "checked": False}
            ],
            "Electronics": [
                {"name": "Phone & Charger", "essential": True, "checked": False},
                {"name": "Power Bank", "essential": True, "checked": False},
                {"name": "Camera", "essential": False, "checked": False}
            ],
            "Documents": [
                {"name": "Passport / Govt ID", "essential": True, "checked": False},
                {"name": "Hotel Bookings & Tickets", "essential": True, "checked": False},
                {"name": "Travel Insurance", "essential": True, "checked": False}
            ],
            "Medicines": [
                {"name": "Personal Prescriptions", "essential": True, "checked": False},
                {"name": "Basic First Aid & Painkillers", "essential": True, "checked": False}
            ],
            "Toiletries": [
                {"name": "Toothbrush & Toothpaste", "essential": True, "checked": False},
                {"name": "Sunscreen & Moisturizer", "essential": True, "checked": False}
            ]
        }
    }


def generate_trip_summary(trip_data: dict, expenses: list, places_visited: list) -> str:
    """Generate an AI travel diary/summary after trip completion."""
    prompt = f"""Write a warm, engaging travel summary for:
Trip: {trip_data.get('source')} to {trip_data.get('destination')}
Duration: {trip_data.get('num_days')} days
Travelers: {trip_data.get('num_travelers')}
Budget: ₹{trip_data.get('budget')}
Total Spent: ₹{sum(e.get('amount', 0) for e in expenses)}
Places Visited: {', '.join(places_visited) if places_visited else 'Key sights'}"""

    messages = [
        {"role": "system", "content": "You are a gifted travel writer."},
        {"role": "user", "content": prompt}
    ]

    res = _call_groq(messages, temperature=0.8, max_tokens=1000, json_mode=False)
    if res:
        return res

    dest = trip_data.get('destination', 'your destination')
    return f"A memorable journey from {trip_data.get('source')} to {dest}! Over {trip_data.get('num_days')} days, you explored local attractions, enjoyed regional food, and managed travel expenses efficiently within budget. Keep exploring new horizons with TripMate!"


def suggest_alternative_itinerary(trip_data: dict, weather_alert: str) -> dict:
    """Suggest alternative activities when weather is bad."""
    dest = trip_data.get('destination', 'Destination')
    return {
        "alternatives": [
            {"name": f"Visit {dest} Art Museum & Cultural Gallery", "description": "Explore indoor historical collections and local art exhibitions.", "estimated_cost": 300, "duration": "2 hours"},
            {"name": f"Indoor Craft & Shopping Center in {dest}", "description": "Browse local handcrafts, souvenir shops, and indoor market halls.", "estimated_cost": 500, "duration": "3 hours"},
            {"name": f"Traditional Cafe & Food Tasting Tour", "description": "Warm up in iconic local cafes and sample signature treats.", "estimated_cost": 400, "duration": "2 hours"}
        ],
        "general_advice": f"Weather alert ({weather_alert}). Stay indoors or visit covered venues in {dest}."
    }


def get_budget_suggestions(budget: float, destination: str, days: int, travelers: int) -> list:
    """Get AI-powered budget saving tips."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Provide 5 money-saving tips for a trip to {destination} for {days} days with budget ₹{budget}. Return JSON: {{\"suggestions\": [\"tip1\", \"tip2\"]}}"}
    ]
    res = _call_groq(messages, temperature=0.7, max_tokens=500, json_mode=True)
    if res and isinstance(res, dict) and res.get('suggestions'):
        return res['suggestions']

    return [
        f"Book accommodation near public transit hubs in {destination} to save on daily travel.",
        "Eat at popular local eateries and street food markets instead of tourist-heavy restaurants.",
        "Purchase city tourist passes for discounted entry to multiple attractions.",
        "Travel during off-peak hours to avoid surge transport fares.",
        "Keep track of daily expenses using TripMate Expense Tracker."
    ]
