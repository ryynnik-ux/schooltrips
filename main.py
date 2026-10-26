import os
import requests
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright


KOULUUN_USER = os.environ["KOULUUN_USER"]
KOULUUN_PASS = os.environ["KOULUUN_PASS"]

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

PASSENGER_ID = os.environ["PASSENGER_ID"]


LOGIN_URL = "https://login.kouluun.fi/Account/Login"
TOKEN_URL = "https://www.kouluun.fi/api/auth/access_token"


def get_access_token():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True
        )

        page = browser.new_page()

        print("Opening login page...")
        page.goto(
            LOGIN_URL,
            wait_until="networkidle",
            timeout=60000
        )

        print("Current URL:", page.url)

        page.locator("#Username").wait_for(
            timeout=60000
        )

        page.fill(
            "#Username",
            KOULUUN_USER
        )

        page.fill(
            "#Password",
            KOULUUN_PASS
        )

        page.screenshot(
            path="before_login.png",
            full_page=True
        )

        print("Submitting login form...")

        page.click('button[type="submit"]')

        page.wait_for_timeout(10000)

        print("URL after login:", page.url)

        page.screenshot(
            path="after_login.png",
            full_page=True
        )

        response = page.request.get(
            TOKEN_URL
        )

        print(
            "Token response status:",
            response.status
        )

        if response.status != 200:
            raise Exception(
                f"Token request failed: {response.status}"
            )

        token_data = response.json()

        browser.close()

        return token_data["accessToken"]


def get_trips(token):
    url = (
        "https://www.kouluun.fi/api/passenger/"
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


def find_next_trip(trips):
    now = datetime.now(timezone.utc)

    future_trips = []

    for trip in trips:
        trip_time = datetime.fromisoformat(
            trip["startDateTime"].replace(
                "Z",
                "+00:00"
            )
        )

        if trip_time > now:
            future_trips.append(trip)

    if not future_trips:
        return None

    future_trips.sort(
        key=lambda x: x["startDateTime"]
    )

    return future_trips[0]


def format_trip(trip):
    trip_time = datetime.fromisoformat(
        trip["startDateTime"].replace(
            "Z",
            "+00:00"
        )
    )

    return (
        "🚕 Seuraava koulukuljetus\n\n"
        f"📅 {trip_time.strftime('%d.%m.%Y %H:%M')}\n"
        f"🚐 Auto: {trip['carName']}\n\n"
        f"📍 Lähtö:\n"
        f"{trip['startPlace']}\n\n"
        f"🏫 Määränpää:\n"
        f"{trip['endPlace']}"
    )


def send_telegram(message):
    response = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": message
        },
        timeout=30
    )

    response.raise_for_status()


def main():
    print("Logging in...")

    token = get_access_token()

    print("Token acquired")

    trips = get_trips(token)

    print(
        f"Trips returned: {len(trips)}"
    )

    next_trip = find_next_trip(trips)

    if next_trip is None:
        send_telegram(
            "Ei tulevia koulukuljetuksia."
        )
        return

    message = format_trip(
        next_trip
    )

    print(message)

    send_telegram(message)

    print("Telegram message sent")


if __name__ == "__main__":
    main()
