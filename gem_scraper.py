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

# --- CONFIGURATION (remains the same) ---
GEM_URL = "https://bidplus.gem.gov.in/all-bids"
# ... (rest of configuration and helper functions are the same) ...

# (Paste your existing KEYWORDS, PROCESSED_FILE, SENDER_EMAIL, etc. and the helper functions here)
# For brevity, I am only showing the changed main function below.
# Please replace the scrape_gem() function in your file with this new one.

def scrape_gem():
    print("--- Checking GeM Portal using Selenium with Stealth ---")
    processed_tenders = load_processed_tenders()
    new_tenders_found = []

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    # Stealth will handle the user-agent, but we can keep one as a fallback
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    driver = None
    try:
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        
        # --- NEW: Apply stealth modifications to the driver ---
        stealth(driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
                )
        # --- END OF NEW PART ---

        driver.get(GEM_URL)
        print("Waiting for page to load...")
        time.sleep(10)
        
        bid_cards = driver.find_elements(By.CSS_SELECTOR, "div.bid_card")
        print(f"Found {len(bid_cards)} bids on the page.")
        # ... (the rest of your scraping loop is the same) ...

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
