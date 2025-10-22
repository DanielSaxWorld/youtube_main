# youtube_scraper_to_csv.py

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import re
import pandas as pd


def get_driver(headless=True):
    """Initializes the Selenium Chrome WebDriver using webdriver-manager."""
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1280x800")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def search_youtube(query, max_channels=15):
    """Searches YouTube and extracts up to `max_channels` unique channels."""
    search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}&sp=EgIQAg%253D%253D"  # filter: channels only
    print(f"\n🔎 Query: {query}")

    driver = get_driver()
    driver.get(search_url)
    time.sleep(3)

    for _ in range(2):
        driver.execute_script("window.scrollBy(0, 1000);")
        time.sleep(2)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    channels = {}
    for a in soup.select("a[href^='/@']"):
        href = a.get("href")
        name = a.text.strip()
        handle_url = f"https://www.youtube.com{href}"

        if name and href and href.startswith("/@") and name not in channels:
            channel_id = None
            try:
                channel_id = get_channel_id_from_handle(handle_url)
            except Exception as e:
                print(f"⚠️ Could not retrieve channel ID for {handle_url}: {e}")

            try:
                last_upload_age = get_last_video_upload_age(handle_url)
                if not last_upload_age:
                    continue  # skip if no video found or upload date couldn't be parsed
            except Exception as e:
                print(f"⚠️ Could not get video upload age for {handle_url}: {e}")
                continue

            if 5 <= last_upload_age <= 10:
                channels[name] = {
                    "query": query,
                    "name": name,
                    "handle_url": handle_url,
                    "channel_id": channel_id,
                    "last_upload_years_ago": last_upload_age
                }

        if len(channels) >= max_channels:
            break

    return list(channels.values())


def get_channel_id_from_handle(handle_url):
    """Loads a YouTube handle page and extracts the UC-based channel ID."""
    driver = get_driver()
    try:
        driver.get(handle_url)
        time.sleep(2.5)
        html = driver.page_source
    finally:
        driver.quit()

    match = re.search(r'<meta itemprop="channelId" content="(UC[\w-]{20,})"', html)
    if match:
        return match.group(1)
    else:
        raise ValueError("Channel ID not found in page.")


def get_last_video_upload_age(handle_url):
    """Gets the age in years of the most recent video on the channel."""
    videos_url = handle_url + "/videos"
    driver = get_driver()
    try:
        driver.get(videos_url)
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, "html.parser")
    finally:
        driver.quit()

    # Find upload times like '5 years ago', '7 years ago', etc.
    age_elements = soup.find_all("span", string=re.compile(r"\d+ (year|years) ago"))
    if not age_elements:
        return None

    age_text = age_elements[0].text.strip()
    match = re.match(r"(\d+)", age_text)
    if match:
        return int(match.group(1))
    return None


def collect_channels_to_csv(queries, per_query=10, output_file="youtube_channels.csv"):
    """Runs searches and saves the results to a CSV."""
    all_data = []
    for query in queries:
        try:
            channels = search_youtube(query, max_channels=per_query)
            all_data.extend(channels)
            for ch in channels:
                print(f"  ✔ {ch['name']} | {ch.get('channel_id', 'N/A')} | Last upload: {ch['last_upload_years_ago']} years ago")
        except Exception as e:
            print(f"❌ Error while processing query '{query}': {e}")

    if all_data:
        df = pd.DataFrame(all_data)
        df.to_csv(output_file, index=False)
        print(f"\n✅ Saved {len(all_data)} channels to {output_file}")
    else:
        print("\n⚠️ No channels were found or saved.")


if __name__ == "__main__":
    search_queries = [
        "fashion haul",
        "small clothing business",
        "makeup tutorial",
        "streetwear style",
        "tech gadgets",
    ]
    collect_channels_to_csv(search_queries, per_query=12)
