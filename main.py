import os
import requests
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright

KOULUUN_USER = os.environ["KOULUUN_USER"]
KOULUUN_PASS = os.environ["KOULUUN_PASS"]

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

TOKEN_URL = "https://www.kouluun.fi/api/auth/access_token"


def get_access_token():
    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled"
            ]
        )

        context = browser.new_context()

        page = context.new_page()

        print("Opening Kouluun.fi...")

        page.goto(
            "https://www.kouluun.fi",
            wait_until="networkidle",
            timeout=60000
        )

        print("Login page URL:")
        print(page.url)

        page.locator("#Username").fill(
            KOULUUN_USER
        )

        page.locator("#Password").fill(
            KOULUUN_PASS
        )

        page.screenshot(
            path="before_login.png",
            full_page=True
        )

        print("Submitting login")

        page.locator(
            'button[type="submit"]'
        ).click()

        page.wait_for_timeout(10000)

        print("Current URL after login:")
        print(page.url)

        page.screenshot(
            path="after_login.png",
            full_page=True
        )

        if "passengers" not in page.url:
            print(
                page.locator("body")
                .inner_text()[:5000]
            )

            raise Exception(
                f"Login failed. Current URL: {page.url}"
            )

        print("Getting access token...")

        response = context.request.get(
            TOKEN_URL
        )

        print(
            "Token status:",
            response.status
        )

        if response.status != 200:
            raise Exception(
                f"Token failed: {response.status}"
            )

        token_json = response.json()

        browser.close()

        print("Token acquired")

        return token_json["accessToken"]


def get_passengers(token):

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(
        "https://www.kouluun.fi/api/passenger",
        headers=headers,
        timeout=30
    )

    print(
        "Passenger status:",
        response.status_code
    )

    response.raise_for_status()

    return response.json()


def get_trips(
    token,
    passenger_id
):

    headers = {
        "Authorization": f"Bearer {token}"
    }

    url = (
        f"https://www.kouluun.fi/api/passenger/"
        f"{passenger_id}/trips"
    )

    response = requests.get(
        url,
        headers=headers,
        timeout=30
    )

    print(
        f"Trips {passenger_id}:",
        response.status_code
    )

    if response.status_code != 200:
        print(response.text)
        return []

    return response.json()


def find_next_trip(trips):

    now = datetime.now(
        timezone.utc
    )

    future = []

    for trip in trips:

        start = datetime.fromisoformat(
            trip["startDateTime"]
            .replace("Z", "+00:00")
        )

        if start > now:
            future.append(trip)

    if not future:
        return None

    future.sort(
        key=lambda x:
        x["startDateTime"]
    )

    return future[0]


def format_trip(trip):

    dt = datetime.fromisoformat(
        trip["startDateTime"]
        .replace("Z", "+00:00")
    )

    return (
        "🚕 Seuraava koulukuljetus\n\n"
        f"📅 {dt.strftime('%d.%m.%Y %H:%M')}\n"
        f"🚐 Auto: {trip.get('carName', '-')}\n\n"
        f"📍 Lähtö:\n"
        f"{trip.get('startPlace', '-')}\n\n"
        f"🏫 Määränpää:\n"
        f"{trip.get('endPlace', '-')}"
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

    token = get_access_token()

    passengers = get_passengers(
        token
    )

    print(
        f"Passengers: {len(passengers)}"
    )

    next_trip = None

    for passenger in passengers:

        passenger_id = passenger["id"]

        print(
            "Checking passenger:",
            passenger_id
        )

        trips = get_trips(
            token,
            passenger_id
        )

        trip = find_next_trip(
            trips
        )

        if trip:
            next_trip = trip
            break

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

    print(
        "Telegram sent successfully"
    )


if __name__ == "__main__":
    main()
