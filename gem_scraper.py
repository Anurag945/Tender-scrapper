# gem_scraper.py (Final version with Selenium-Stealth)

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# --- NEW: Import the stealth library ---
from selenium_stealth import stealth

# --- CONFIGURATION ---
GEM_URL = "https://bidplus.gem.gov.in/all-bids"
KEYWORDS = ["amc", "laptop", "dell", "lenovo", "hp", "server", "switch", "networking", "cctv"]
PROCESSED_FILE = "processed_gem.txt"

# --- EMAIL CONFIGURATION (Read from GitHub Secrets) ---
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")


# --- HELPER FUNCTIONS ---
def load_processed_tenders():
    """Reads the set of processed tender numbers from our file."""
    try:
        with open(PROCESSED_FILE, 'r') as f:
            return set(line.strip() for line in f)
    except FileNotFoundError:
        open(PROCESSED_FILE, 'w').close()
        return set()

def save_processed_tender(tender_no):
    """Appends a new tender number to our file."""
    with open(PROCESSED_FILE, 'a') as f:
        f.write(tender_no + '\n')

def send_email_alert(new_bids):
    """Formats and sends an email with the list of new bids."""
    if not all([SENDER_EMAIL, SENDER_PASSWORD, RECEIVER_EMAIL]):
        print("Email credentials are not set. Skipping email.")
        return
        
    message = MIMEMultipart("alternative")
    message["Subject"] = f"GeM Bid Alert: {len(new_bids)} New Bids Found"
    message["From"] = SENDER_EMAIL
    message["To"] = RECEIVER_EMAIL

    html_body = "<html><body><p>The following new bids were found on the GeM portal:</p>"
    html_body += '<table border="1" style="border-collapse: collapse; width: 100%;">'
    html_body += '<tr><th style="padding: 8px; text-align: left;">Bid No.</th><th style="padding: 8px; text-align: left;">Item(s)</th><th style="padding: 8px; text-align: left;">End Date</th><th style="padding: 8px; text-align: left;">Link</th></tr>'
    for bid in new_bids:
        html_body += f'<tr><td style="padding: 8px;">{bid["tender_no"]}</td><td style="padding: 8px;">{bid["notification"]}</td><td style="padding: 8px;">{bid["last_date"]}</td><td style="padding: 8px;"><a href="{bid["link"]}">Link to Bid</a></td></tr>'
    html_body += "</table></body></html>"
    message.attach(MIMEText(html_body, "html"))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, message.as_string())
        server.quit()
        print(f"Successfully sent email alert for {len(new_bids)} GeM bids.")
    except Exception as e:
        print(f"Failed to send email for GeM: {e}")

# --- MAIN LOGIC ---
def scrape_gem():
    print("--- Checking GeM Portal using Selenium with Stealth ---")
    processed_tenders = load_processed_tenders()
    new_tenders_found = []

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    driver = None
    try:
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        
        # --- APPLYING STEALTH MODIFICATIONS ---
        stealth(driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
                )
        # --- END OF STEALTH PART ---

        driver.get(GEM_URL)
        print("Waiting for page to load...")
        time.sleep(10)
        
        bid_cards = driver.find_elements(By.CSS_SELECTOR, "div.bid_card")
        print(f"Found {len(bid_cards)} bids on the page.")

        for card in bid_cards[:15]:
            try:
                tender_no = card.find_element(By.CSS_SELECTOR, "div.bid_no a").text
                notification = card.find_element(By.CSS_SELECTOR, "div.block_header p a").text
                last_date = card.find_element(By.CSS_SELECTOR, "div.end_date span").text
                link = card.find_element(By.CSS_SELECTOR, "div.bid_no a").get_attribute('href')
                
                if tender_no in processed_tenders:
                    continue

                if any(keyword in notification.lower() for keyword in KEYWORDS):
                    print(f"GeM: Found new bid -> {tender_no}")
                    new_tenders_found.append({
                        "tender_no": tender_no, "notification": notification,
                        "last_date": last_date, "link": link
                    })
                    save_processed_tender(tender_no)
            except Exception:
                continue
    except Exception as e:
        print(f"An error occurred during GeM scraping: {e}")
    finally:
        if driver:
            driver.quit()

    if new_tenders_found:
        send_email_alert(new_tenders_found)
    else:
        print("No new bids found on GeM.")


if __name__ == "__main__":
    scrape_gem()
