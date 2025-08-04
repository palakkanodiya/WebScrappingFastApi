import time
import pandas as pd
from pymongo import MongoClient
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


client = MongoClient("mongodb://localhost:27017/")
db = client["walmart_scraped"]
collection = db["consoles"]

# ---- Chrome Options ----
options = uc.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--disable-gpu")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--lang=en-US,en")
options.add_argument("--window-size=1920,1080")
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
)

# ---- Start Chrome Browser ----
driver = uc.Chrome(options=options, headless=False)

# ---- Walmart Product URL to scrape ----
# product_url = "https://www.walmart.com/ip/PlayStation-5-Digital-Console-Slim/5113183757"
# product_url = "https://www.walmart.com/ip/TCL-NXTPAPER-11-Plus/14687819013"
product_url = "https://www.walmart.com/ip/Wrangler-Men-s-and-Big-Men-s-Regular-Fit-Short-Sleeve-Western-Shirt-Sizes-S-5XL/13284554901?classType=VARIANT&adsRedirect=true"
# product_url = "https://www.kroger.com/p/kroger-marshmallows/0001111009386?fulfillment=PICKUP"
driver.get(product_url)

# ---- Handle CAPTCHA manually ----
time.sleep(3)
if "captcha" in driver.page_source.lower():
    print("CAPTCHA detected! Solve it manually.")
    input("Press ENTER after solving CAPTCHA...")

# ---- Utility Functions ----

def scroll_to_element(selector, timeout=10):
    try:
        elem = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        driver.execute_script("arguments[0].scrollIntoView({behavior:'smooth', block:'center'});", elem)
        time.sleep(2)
        return elem
    except Exception:
        return None

def scroll_to_element_by_id(element_id):
    try:
        driver.execute_script(f"document.getElementById('{element_id}').scrollIntoView();")
        time.sleep(2)
        return True
    except Exception:
        return False

def safe_find_text_by_css(selectors, timeout=5):
    # Tries multiple CSS selectors, returns first non-empty text or 'N/A'
    if isinstance(selectors, str):
        selectors = [selectors]
    for selector in selectors:
        try:
            elem = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            text = elem.text.strip()
            if text:
                return text
        except:
            continue
    return "N/A"

def extract_colors(driver):
    color_names = []
    try:
        selectors = [
            'ul[data-tl-id*="color"] button span',
            'ul[data-tl-id*="color"] label span',
            'div[data-automation-id="color-picker"] label span',
            '[data-tl-id*="color"] button span',
            '[data-tl-id*="color"] label span',
            '[aria-label*="Color"]',
            'button[aria-checked="true"] span',
            '[itemprop="color"]',
        ]

        for sel in selectors:
            elems = driver.find_elements(By.CSS_SELECTOR, sel)
            for elem in elems:
                name = elem.text.strip()
                if name and name.lower() not in [c.lower() for c in color_names]:
                    color_names.append(name)
            if color_names:
                break

        if not color_names:
            imgs = driver.find_elements(By.CSS_SELECTOR,
                                       'img[data-testid*="swatch"], img[alt*="color"], img[alt*="Color"], img[alt*="colour"]')
            for img in imgs:
                alt = img.get_attribute('alt') or img.get_attribute('title')
                if alt:
                    alt_clean = alt.replace('Color', '').replace('Swatch', '').strip()
                    if alt_clean and alt_clean.lower() not in [c.lower() for c in color_names]:
                        color_names.append(alt_clean)

        if not color_names:
            color_names.append("N/A")
    except Exception:
        color_names = ["N/A"]
    return color_names

def extract_sizes(driver):
    size_names = []
    try:
        size_selectors = [
            'ul[data-tl-id*="size"] button span',
            'ul[data-tl-id*="size"] label span',
            'div[data-automation-id="size-picker"] label',
            'ul[data-tl-id*="variant"] button span',
            'ul[data-tl-id*="variant"] label span',
            '[aria-label*="Size"]',
            'button[aria-checked="true"] span',
        ]

        for sel in size_selectors:
            elems = driver.find_elements(By.CSS_SELECTOR, sel)
            for elem in elems:
                txt = elem.text.strip()
                if txt and txt.lower() != "select" and txt.lower() not in [x.lower() for x in size_names]:
                    size_names.append(txt)
            if size_names:
                break

        if not size_names:
            selected = driver.find_elements(By.CSS_SELECTOR, '[aria-checked="true"] span')
            for s in selected:
                txt = s.text.strip()
                if txt and txt.lower() not in [x.lower() for x in size_names]:
                    size_names.append(txt)

        if not size_names:
            size_names.append("N/A")
    except Exception:
        size_names = ["N/A"]

    return size_names

# ---- Data Dictionary ----
product = {
    "title": safe_find_text_by_css(['h1.prod-ProductTitle', 'h1[itemprop="name"]'], timeout=15),
    "price": safe_find_text_by_css(['span.price-characteristic', 'span[itemprop="price"]', 'span.price-group'], timeout=10),
    "images": [],
    # "about_this_item": "N/A",
    "colors": ["N/A"],
    "sizes": ["N/A"],
    "product_url": product_url,
    "related_links": [],
}

product["colors"] = extract_colors(driver)


product["sizes"] = extract_sizes(driver)


try:
    gallery_elem = scroll_to_element('div[data-testid="media-gallery"]')
    image_urls = []
    image_set = set()

    if gallery_elem:
        thumbs = driver.find_elements(By.CSS_SELECTOR, 'img[data-testid="media-gallery-thumbnail-image"]')
        for thumb in thumbs:
            if len(image_urls) >=5:
                break
            try:
                driver.execute_script("arguments[0].scrollIntoView({behavior:'smooth', block:'center'});", thumb)
                time.sleep(1)
                thumb.click()
                time.sleep(1.5)
                main_img = driver.find_element(By.CSS_SELECTOR, 'div[data-testid="media-gallery"] img[data-testid="media-gallery-image"]')
                src = main_img.get_attribute("src") or main_img.get_attribute("data-src")
                if src and src not in image_set:
                    image_set.add(src)
                    image_urls.append(src)
            except Exception:
                continue
        # fallback if less than 5
        if len(image_urls) <5:
            imgs = gallery_elem.find_elements(By.TAG_NAME, 'img')
            for img in imgs:
                src = img.get_attribute('src') or img.get_attribute('data-src')
                if src and src not in image_set:
                    image_set.add(src)
                    image_urls.append(src)
                if len(image_urls) >=5:
                    break
    if not image_urls:
        imgs = driver.find_elements(By.CSS_SELECTOR, 'img')
        for img in imgs:
            src = img.get_attribute('src') or img.get_attribute('data-src')
            if src and src not in image_set and any(ext in src.lower() for ext in ['.jpg','.png','.gif','.webp']):
                image_set.add(src)
                image_urls.append(src)
            if len(image_urls) >=5:
                break
    product["images"] = image_urls
    print(f"Product gallery images: {len(product['images'])} extracted (max 5).")
except Exception as e:
    print(f"Error extracting images: {e}")

try:
    scroll_to_element_by_id("product-description-section")
    desc_container = WebDriverWait(driver, 12).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="product-description-section"]'))
    )
    details = []

    # extracting all bullet points inside
    for ul in desc_container.find_elements(By.XPATH, ".//ul | .//ol"):
        for li in ul.find_elements(By.TAG_NAME, 'li'):
            line = li.text.strip()
            if line:
                details.append(line)

    # also add paragraphs not already captured
    for p in desc_container.find_elements(By.TAG_NAME, 'p'):
        line = p.text.strip()
        if line and line not in details:
            details.append(line)

    # fallback: exclude general headings from full container text
    if not details:
        all_lines = [line.strip() for line in desc_container.text.split('\n') if line.strip()]
        headings = ["about this item", "product details"]
        details = [l for l in all_lines if l.lower() not in headings]

    about_text = "\n".join(details).strip()
    product["about_this_item"] = about_text if about_text else "N/A"
    print("About This Item content extracted.")
except Exception as e:
    product["about_this_item"] = "N/A"
    print(f"Failed to extract About This Item: {e}")

# ---- Related Links ----
try:
    links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/ip/"]')
    unique_links = set()
    for a in links:
        href = a.get_attribute("href")
        if href and "/ip/" in href:
            unique_links.add(href.split("?")[0])
    product["related_links"] = list(unique_links)
except Exception as e:
    print("Related links not found:", e)

# ---- Print all scraped data ----
print("\nProduct Details:")
for k, v in product.items():
    if isinstance(v, list):
        print(f"{k.capitalize()}: {len(v)} items -> {v}")
    else:
        print(f"{k.capitalize()}: {v}")

# ---- Save to MongoDB ----
try:
    collection.insert_one(product)
    print("Saved to MongoDB")
except Exception as e:
    print("Error saving to MongoDB:", e)

# ---- Save to CSV ----
csv_file = "walmart_data.csv"
try:
    df = pd.DataFrame([product])
    df.to_csv(csv_file, index=False)
    print(f"Saved to CSV: {csv_file}")
except Exception as e:
    print("Error saving to CSV:", e)

# ---- Quit Browser ----
driver.quit()
  