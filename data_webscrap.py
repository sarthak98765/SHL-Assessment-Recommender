import time
import csv
import asyncio
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import chromedriver_autoinstaller

chromedriver_autoinstaller.install()

BASE_URLS = [
    ("Type 1", "https://www.shl.com/solutions/products/product-catalog/?start={}&type=1&type=1"),
    ("Type 2", "https://www.shl.com/solutions/products/product-catalog/?start={}&type=1&type=2"),
]

options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("user-agent=Mozilla/5.0")

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 15)

def accept_cookies():
    try:
        cookie_btn = wait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
        cookie_btn.click()
        print("✅ Cookies accepted.")
    except:
        print("ℹ️ Cookie banner not shown.")

def get_details_from_detail(url):
    try:
        detail_driver = webdriver.Chrome(options=options)
        detail_wait = WebDriverWait(detail_driver, 10)

        full_url = "https://www.shl.com" + url if url.startswith("/") else url
        detail_driver.get(full_url)
        detail_wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".product-catalogue-training-calendar__row")))
        time.sleep(1)

        rows = detail_driver.find_elements(By.CSS_SELECTOR, ".product-catalogue-training-calendar__row")
        info = {"Duration": "N/A", "Job Description": "N/A", "Job Levels": "N/A", "Languages": "N/A"}

        for row in rows:
            try:
                heading = row.find_element(By.TAG_NAME, "h4").text.strip().lower()
                value = row.find_element(By.TAG_NAME, "p").text.strip()
                if "assessment length" in heading:
                    info["Duration"] = value.split("=")[-1].strip() if "=" in value else value
                elif "description" in heading:
                    info["Job Description"] = value
                elif "job levels" in heading:
                    info["Job Levels"] = value
                elif "languages" in heading:
                    info["Languages"] = value
            except:
                continue

        detail_driver.quit()
        return info
    except Exception as e:
        print(f"❌ Detail fetch error from {url}: {e}")
        return {"Duration": "N/A", "Job Description": "N/A", "Job Levels": "N/A", "Languages": "N/A"}

def get_main_info_from_row(row):
    try:
        tds = row.find_elements(By.TAG_NAME, "td")
        remote = "Yes" if tds[1].find_elements(By.CSS_SELECTOR, ".-yes") else "No"
        adaptive = "Yes" if tds[2].find_elements(By.CSS_SELECTOR, ".-yes") else "No"
        type_tags = tds[3].find_elements(By.CSS_SELECTOR, "span.product-catalogue__key")
        test_type = " ".join(tag.text.strip() for tag in type_tags if tag.text.strip())
        return remote, adaptive, test_type
    except:
        return "N/A", "N/A", "N/A"

async def scrape_page(url, executor):
    print(f"\n🌐 Scraping catalog page: {url}")
    driver.get(url)

    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tr")))
        time.sleep(1)
    except TimeoutException:
        print(f"⚠️ Timeout on catalog page: {url}")
        return []

    rows = driver.find_elements(By.CSS_SELECTOR, "table tr[data-entity-id]")
    if not rows:
        print("❌ Skipped: Not a valid assessment page.")
        return []

    print(f"✅ Found {len(rows)} assessments.")
    tasks = []
    data = []

    for row in rows:
        try:
            link_tag = row.find_element(By.CSS_SELECTOR, "td a")
            name = link_tag.text.strip()
            link = link_tag.get_attribute("href")
            remote, adaptive, test_type = get_main_info_from_row(row)

            loop = asyncio.get_event_loop()
            task = loop.run_in_executor(executor, get_details_from_detail, link)
            tasks.append((name, link, remote, adaptive, test_type, task))
        except Exception as e:
            print(f"❌ Error reading row: {e}")
            continue

    for i, (name, link, remote, adaptive, test_type, task) in enumerate(tasks):
        details = await task
        print(f"🔍 ({i + 1}/{len(tasks)}) {name}")
        data.append({
            "Assessment Name": name,
            "URL": link,
            "Remote Testing": remote,
            "Adaptive/IRT": adaptive,
            "Test Type": test_type,
            "Duration": details["Duration"],
            "Job Description": details["Job Description"],
            "Job Levels": details["Job Levels"],
            "Languages": details["Languages"]
        })

    return data

def save_to_csv(all_data, filename="yrrrrr.csv"):
    keys = [
        "Assessment Name", "URL", "Remote Testing", "Adaptive/IRT",
        "Test Type", "Duration", "Job Description", "Job Levels", "Languages"
    ]
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(all_data)
    print(f"\n📦 Data saved to '{filename}' with {len(all_data)} rows.")

async def main():
    accept_cookies()
    all_data = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        for label, base_url in BASE_URLS:
            print(f"\n==================== SCRAPING {label} ====================")
            for start in range(0, 380, 12):
                page_url = base_url.format(start)
                retries = 3
                page_data = []

                for attempt in range(1, retries + 1):
                    page_data = await scrape_page(page_url, executor)
                    if page_data:
                        break
                    print(f"🔁 Retry {attempt}/{retries} for {page_url}")
                    time.sleep(2)

                if not page_data:
                    print(f"🚫 No data found after {retries} attempts at {page_url}, stopping pagination.")
                    break

                all_data.extend(page_data)

    save_to_csv(all_data)
    driver.quit()

if __name__ == "__main__":
    asyncio.run(main())
