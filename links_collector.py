from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import json
import time

CHROME_DRIVER_PATH = ""

URL = '' 

def setup_driver():
    s = Service(CHROME_DRIVER_PATH)
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument('--ignore-ssl-errors')
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/119.0.0.0 Safari/537.36")
    return webdriver.Chrome(service=s, options=options)

def extract_video_links(browser):
    videos = browser.find_elements(By.CSS_SELECTOR, 'ytd-video-renderer h3 a')
    video_data = []

    for index, video in enumerate(videos, start=1):
        title = video.get_attribute('title')
        url = video.get_attribute('href')
        if url:
            video_data.append({
                "index": index,
                "title": title.strip() if title else "N/A",
                "url": url.strip()
            })

    return video_data

try:
    browser = setup_driver()
    browser.get(URL)
    browser.maximize_window()
    time.sleep(2)

    for _ in range(400): 
        browser.execute_script("window.scrollBy(0,500)") 
        time.sleep(0.5)

    time.sleep(3)

    file_name = "links.json"

    video_links = extract_video_links(browser)
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(video_links, f, ensure_ascii=False, indent=2)

    print("Extracted", len(video_links), "video links.")
    print(f'Data saved to ${file_name}')

finally:
    browser.quit()
