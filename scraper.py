# scraper.py (for LNMIIT)

import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import urllib3
import os # <-- Import the 'os' module to read secrets

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATION for LNMIIT ---
URL = "https://lnmiit.ac.in/tenders/"
KEYWORDS = ["amc", "laptop", "dell", "lenovo", "hp", "server", "switch", "networking"]
PROCESSED_FILE = "processed_lnmiit.txt"

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
        # Create the file if it doesn't exist on the first run
        open(PROCESSED_FILE, 'w').close()
        return set()

def save_processed_tender(tender_no):
    """Appends a new tender number to our file."""
    with open(PROCESSED_FILE, 'a') as f:
        f.write(tender_no + '\n')

def send_email_alert(new_tenders):
    """Formats and sends an email with the list of new tenders."""
    if not all([SENDER_EMAIL, SENDER_PASSWORD, RECEIVER_EMAIL]):
        print("Email credentials are not set. Skipping email.")
        return

    message = MIMEMultipart("alternative")
    message["Subject"] = f"LNMIIT Tender Alert: {len(new_tenders)} New Tenders Found"
    message["From"] = SENDER_EMAIL
    message["To"] = RECEIVER_EMAIL

    html_body = "<html><body><p>The following new tenders were found on the LNMIIT website:</p>"
    html_body += '<table border="1" style="border-collapse: collapse; width: 100%;">'
    html_body += '<tr><th style="padding: 8px; text-align: left;">Tender No.</th><th style="padding: 8px; text-align: left;">Notification</th><th style="padding: 8px; text-align: left;">Last Date</th></tr>'
    for tender in new_tenders:
        html_body += f'<tr><td style="padding: 8px;">{tender["tender_no"]}</td><td style="padding: 8px;">{tender["notification"]}</td><td style="padding: 8px;">{tender["last_date"]}</td></tr>'
    html_body += "</table></body></html>"
    message.attach(MIMEText(html_body, "html"))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, message.as_string())
        server.quit()
        print(f"Successfully sent email alert for {len(new_tenders)} LNMIIT tenders.")
    except Exception as e:
        print(f"Failed to send email for LNMIIT: {e}")

# --- MAIN LOGIC ---
def scrape_lnmiit():
    print("--- Checking LNMIIT ---")
    processed = load_processed_tenders()
    found = []
    try:
        response = requests.get(URL, verify=False)
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table')
        if not table:
            print("Could not find table on LNMIIT page.")
            return
            
        rows = table.find_all('tr')[1:]
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 4: continue
            notification = cols[1].get_text(strip=True)
            tender_no = cols[2].get_text(strip=True)
            last_date = cols[3].get_text(strip=True)

            if tender_no in processed: continue
            if any(k in notification.lower() for k in KEYWORDS):
                print(f"LNMIIT: Found new tender -> {tender_no}")
                found.append({"tender_no": tender_no, "notification": notification, "last_date": last_date})
                save_processed_tender(tender_no)
    except Exception as e:
        print(f"Error scraping LNMIIT: {e}")

    if found:
        send_email_alert(found)
    else:
        print("No new tenders found on LNMIIT.")

if __name__ == "__main__":
    scrape_lnmiit()
