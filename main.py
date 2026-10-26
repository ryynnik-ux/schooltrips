import os
import requests
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright

USERNAME = os.environ["KOULUUN_USER"]
PASSWORD = os.environ["KOULUUN_PASS"]

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

PASSENGER_ID = os.environ["PASSENGER_ID"]

TOKEN_URL = "https://www.kouluun.fi/api/auth/access_token"


def get_access_token():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        page = browser.new_page()

        page.goto("https://www.kouluun.fi")

        page.fill("#Username", USERNAME)
        page.fill("#Password", PASSWORD)

        page.click('button[type="submit"]')

        page.wait_for_url("**/loggedin", timeout=30000)

        response = page.request.get(TOKEN_URL)

        response.raise_for_status()

        token = response.json()["accessToken"]

        browser.close()

        return token


def get_trips(token):
    url = (
        f"https://www.kouluun.fi/api/passenger/"
        f"{PASSENGER_ID}/trips"
    )

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def next_trip(trips):
    now = datetime.now(timezone.utc)

    future = []

    for trip in trips:
        trip_time = datetime.fromisoformat(
            trip["startDateTime"].replace("Z", "+00:00")
        )

        if trip_time > now:
            future.append(trip)

    if not future:
        return None

    future.sort(
        key=lambda x: x["startDateTime"]
    )

    return future[0]


def format_trip(trip):
    dt = datetime.fromisoformat(
        trip["startDateTime"].replace("Z", "+00:00")
    )

    return (
        "🚕 Seuraava koulukuljetus\n\n"
        f"📅 {dt.strftime('%d.%m.%Y %H:%M')}\n"
        f"🚐 {trip['carName']}\n\n"
        f"📍 Lähtö\n"
        f"{trip['startPlace']}\n\n"
        f"🏫 Määränpää\n"
        f"{trip['endPlace']}"
    )


def send_telegram(message):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": message
        },
        timeout=30,
    )


def main():
    token = get_access_token()

    trips = get_trips(token)

    trip = next_trip(trips)

    if trip:
        send_telegram(format_trip(trip))


if __name__ == "__main__":
    main()
