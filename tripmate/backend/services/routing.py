import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ORS_API_KEY")


def get_route(source, destination):

    url = "https://api.openrouteservice.org/v2/directions/driving-car"

    headers = {
        "Authorization": API_KEY,
        "Content-Type": "application/json"
    }

    body = {
        "coordinates": [

            [source["longitude"], source["latitude"]],

            [destination["longitude"], destination["latitude"]]

        ]
    }

    response = requests.post(
        url,
        json=body,
        headers=headers
    )

    return response.json()