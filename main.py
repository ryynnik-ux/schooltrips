def get_access_token():
    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True
        )

        context = browser.new_context()

        page = context.new_page()

        print("Opening login page...")

        page.goto(
            "https://login.kouluun.fi/Account/Login",
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
                timeout=10000
            )

            user_selector = "#Username"
            pass_selector = "#Password"

        except Exception:

            print(
                "Username field not found, dumping page..."
            )

            print(page.title())

            print(
                page.locator("body")
                .inner_text()[:3000]
            )

            page.screenshot(
                path="login_page_error.png",
                full_page=True
            )

            raise

        print("Filling credentials...")

        page.fill(
            user_selector,
            KOULUUN_USER
        )

        page.fill(
            pass_selector,
            KOULUUN_PASS
        )

        page.screenshot(
            path="before_submit.png",
            full_page=True
        )

        print("Submitting login...")

        page.click(
            'button[type="submit"]'
        )

        page.wait_for_timeout(10000)

        print(
            "After login URL:",
            page.url
        )

        page.screenshot(
            path="after_login.png",
            full_page=True
        )

        print(
            "Getting access token..."
        )

        response = context.request.get(
            "https://www.kouluun.fi/api/auth/access_token"
        )

        print(
            "Token status:",
            response.status
        )

        print(
            "Token response:",
            response.text()[:1000]
        )

        response.raise_for_status()

        token_data = response.json()

        browser.close()

        return token_data["accessToken"]
