print("FILE LOADED")
def get_access_token():

    print("Opening login page...")

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True
        )

        context = browser.new_context()

        page = context.new_page()

        page.goto(
            "https://login.kouluun.fi/Account/Login",
            wait_until="domcontentloaded",
            timeout=60000
        )

        print("Current URL:", page.url)

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

        page.screenshot(
            path="before_login.png",
            full_page=True
        )

        print("Submitting login...")

        page.click(
            'button[type="submit"]'
        )

        page.wait_for_timeout(5000)

        print("After login URL:")
        print(page.url)

        print("PAGE TITLE:")
        print(page.title())

        print("BODY TEXT:")
        print(
            page.locator("body")
            .inner_text()[:10000]
        )

        page.screenshot(
            path="after_login.png",
            full_page=True
        )

        print("Requesting token...")

        response = context.request.get(
            "https://www.kouluun.fi/api/auth/access_token"
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
        except Exception as e:
            print(e)

        if response.status != 200:
            raise Exception(
                f"Token request failed: {response.status}"
            )

        token_json = response.json()

        print("Parsed token JSON:")
        print(token_json)

        if not token_json.get("accessToken"):
            raise Exception(
                f"Login failed, accessToken missing. Response: {token_json}"
            )

        browser.close()

        print("Token acquired")

        return token_json["accessToken"]
print("BEFORE MAIN")

if __name__ == "__main__":
    print("CALLING MAIN")
    main()
