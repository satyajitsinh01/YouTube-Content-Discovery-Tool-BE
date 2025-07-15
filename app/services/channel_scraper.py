import os
import re
import time
from urllib.parse import urlparse, parse_qs, unquote
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from twocaptcha import TwoCaptcha

class ChannelScraper:
    def __init__(self):
        chrome_binary_path = os.getenv("CHROME_BINARY_PATH")
        chromedriver_path = os.getenv("CHROMEDRIVER_PATH")
        api_key = os.getenv("APIKEY_2CAPTCHA")

        options = Options()
        if chrome_binary_path:
            options.binary_location = chrome_binary_path
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        try:
            if chromedriver_path and os.path.exists(chromedriver_path):
                service = Service(executable_path=chromedriver_path)
                self.driver = webdriver.Chrome(service=service, options=options)
            else:
                self.driver = webdriver.Chrome(options=options)

            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except Exception as e:
            print(f"[Error] Chrome driver init failed: {e}")
            raise

        self.solver = TwoCaptcha(api_key) if api_key else None

    def close(self):
        try:
            self.driver.quit()
        except:
            pass

    def solve_recaptcha(self, site_key, page_url):
        if not self.solver:
            return None
        try:
            result = self.solver.recaptcha(sitekey=site_key, url=page_url)
            return result['code']
        except Exception as e:
            print(f"[Captcha Error] {e}")
            return None

    def _close_overlays(self):
        try:
            buttons = self.driver.find_elements(By.XPATH, "//button[contains(@aria-label,'Close') or contains(@aria-label,'Dismiss')]")
            for btn in buttons:
                if btn.is_displayed():
                    self.driver.execute_script("arguments[0].click();", btn)
                    time.sleep(0.5)
        except:
            pass

    def _extract_email(self):
        try:
            links = self.driver.find_elements(By.XPATH, "//a[starts-with(@href,'mailto:')]")
            for link in links:
                email = link.get_attribute("href").replace("mailto:", "").split("?")[0]
                if self._is_valid_email(email):
                    return email
        except:
            pass

        try:
            email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
            matches = re.findall(email_pattern, self.driver.page_source)
            for match in matches:
                if self._is_valid_email(match):
                    return match
        except:
            pass

        return None

    def _is_valid_email(self, email):
        blocked = ["example.com", "test.com", "domain.com"]
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
          return False
        if email.startswith("wght@"):
          return False
        return not any(b in email.lower() for b in blocked)


    def _is_useful_social_link(self, url):
        social_domains = [
            "instagram.com", "facebook.com", "twitter.com", "x.com", "linkedin.com",
            "t.me", "threads.net", "discord.gg", "patreon.com", "onlyfans.com",
            "github.com", "pinterest.com", "linktr.ee", "soundcloud.com", "tiktok.com"
        ]
        return (
            url.startswith("http") and any(domain in url for domain in social_domains)
        )

    def _extract_redirected_links(self):
        links = set()
        try:
            redirect_elements = self.driver.find_elements(By.CSS_SELECTOR, "yt-channel-external-link-view-model a[href*='youtube.com/redirect']")
            for el in redirect_elements:
                href = el.get_attribute("href")
                if href:
                    parsed_url = urlparse(href)
                    qs = parse_qs(parsed_url.query)
                    if 'q' in qs:
                        actual_url = unquote(qs['q'][0])
                        if self._is_useful_social_link(actual_url):
                            links.add(actual_url)
        except Exception as e:
            print(f"[Redirect Link Error] {e}")
        return links

    def extract_from_channel(self, channel_url):
        # Convert handle to full URL if needed
        if channel_url.startswith("@"): 
            channel_url = f"https://www.youtube.com/{channel_url}"
        about_url = f"{channel_url.rstrip('/')}/about"
        try:
            self.driver.get(about_url)
            WebDriverWait(self.driver, 20).until(lambda d: d.execute_script("return document.readyState") == "complete")

            if "recaptcha" in self.driver.page_source.lower():
                match = re.search(r'data-sitekey="(.+?)"', self.driver.page_source)
                if match:
                    token = self.solve_recaptcha(match.group(1), about_url)
                    if token:
                        self.driver.execute_script("document.getElementById('g-recaptcha-response').innerHTML = arguments[0];", token)
                        time.sleep(3)
                        self.driver.refresh()

            self._close_overlays()
            email = self._extract_email()

            links = self._extract_redirected_links()

            return {"email": email, "links": list(links)}
        except Exception as e:
            print(f"[Error] {channel_url}: {e}")
            return {"email": None, "links": []}
