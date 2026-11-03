import os
import requests
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright

print("MAIN.PY STARTED")

KOULUUN_USER = os.environ["KOULUUN_USER"]
KOULUUN_PASS = os.environ["KOULUUN_PASS"]

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

LOGIN_URL = "https://login.kouluun.fi/Account/Login"
TOKEN_URL = "https://www.kouluun.fi/api/auth/access_token"


def get_access_token():

    print("Opening login page...")

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True
        )

        context = browser.new_context()

        page = context.new_page()

        page.goto(
            LOGIN_URL,
            wait_until="domcontentloaded",
            timeout=60000
        )

        print("Current URL:", page.url)

        page.screenshot(
            path="before_login.png",
            full_page=True
        )

        try:
            page.wait_for_selector(
                "#Username",
                timeout=15000
            )

            page.fill(
                "#Username",
                KOULUUN_USER
            )

            page.fill(
                "#Password",
                KOULUUN_PASS
            )

        except Exception as e:

            print("USERNAME FIELD NOT FOUND")
            print(str(e))

            print("PAGE TITLE:")
            print(page.title())

            print("PAGE TEXT:")
            print(
                page.locator("body")
                .inner_text()[:5000]
            )

            page.screenshot(
                path="login_error.png",
                full_page=True
            )

            raise

        print("Submitting login...")

        page.click(
            'button[type="submit"]'
        )

        page.wait_for_timeout(10000)

        print("After login URL:")
        print(page.url)

        page.screenshot(
            path="after_login.png",
            full_page=True
        )

        print("Requesting token...")

        response = context.request.get(
            TOKEN_URL
        )

        print(
            "Token response status:",
            response.status
        )

        print(
            "Token response body:"
        )

        try:
            print(response.text())
        except:
            pass

        response.raise_for_status()

        token_json = response.json()

        browser.close()

        if "accessToken" not in token_json:
            raise Exception(
                "accessToken not found"
            )

        print("Token acquired")

        return token_json["accessToken"]


def get_passengers(token):

    print("Getting passengers...")

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

    print(
        "Passenger response:"
    )

    print(response.text)

    response.raise_for_status()

    return response.json()


def get_trips(token, passenger_id):

    print(
        f"Getting trips for {passenger_id}"
    )

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(
        f"https://www.kouluun.fi/api/passenger/{passenger_id}/trips",
        headers=headers,
        timeout=30
    )

    print(
        "Trips status:",
        response.status_code
    )

    print(
        "Trips response:"
    )

    print(response.text[:3000])

    if response.status_code != 200:
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
        key=lambda t:
        t["startDateTime"]
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

    print("Sending Telegram message...")

    response = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": message
        },
        timeout=30
    )

    print(
        "Telegram status:",
        response.status_code
    )

    print(
        "Telegram response:"
    )

    print(response.text)

    response.raise_for_status()


def main():

    print("MAIN FUNCTION STARTED")

    token = get_access_token()

    passengers = get_passengers(
        token
    )

    print(
        f"Passengers found: {len(passengers)}"
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

        print(
            "No future trips found"
        )

        send_telegram(
            "Ei tulevia koulukuljetuksia."
        )

        return

    message = format_trip(
        next_trip
    )

    print("MESSAGE:")

    print(message)

    send_telegram(message)

    print("DONE")


if __name__ == "__main__":

    print("ENTERING MAIN")

    main()
