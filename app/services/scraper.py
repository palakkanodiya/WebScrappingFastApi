import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def scrape_walmart(url, headless=False):
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

    driver = uc.Chrome(options=options, headless=headless)
    try:
        driver.get(url)
        time.sleep(5)

        # Debug: Page preview
        print(" PAGE SOURCE PREVIEW ")
        print(driver.page_source[:1500])
        print("----")

        if any(term in driver.page_source.lower() for term in ["captcha", "are you a human", "verify you are human", "access denied"]):
            print("CAPTCHA or bot detection triggered! Please solve it manually.")
            input("Press ENTER after solving CAPTCHA and page loads correctly...")

        def safe_find_text_by_css(selectors, timeout=5):
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
                except Exception:
                    continue
            return "N/A"

        def extract_colors():
            color_names = []
            try:
                selectors = [
                    '[data-testid*="swatch"]',
                    '[data-testid*="color-swatch"]',
                    '[aria-label*="Color"] span',
                    '[itemprop="color"]',
                ]
                for sel in selectors:
                    elems = driver.find_elements(By.CSS_SELECTOR, sel)
                    for elem in elems:
                        txt = elem.text.strip()
                        if txt and txt.lower() not in [c.lower() for c in color_names]:
                            color_names.append(txt)
                    if color_names:
                        break
                return color_names or ["N/A"]
            except Exception:
                return ["N/A"]

        def extract_sizes():
            size_names = []
            try:
                selectors = [
                    '[aria-label*="Size"] span',
                    'ul[data-tl-id*="variant"] button span',
                    'div[data-automation-id="size-picker"] label',
                    'button[aria-checked="true"] span'
                ]
                for sel in selectors:
                    elems = driver.find_elements(By.CSS_SELECTOR, sel)
                    for elem in elems:
                        txt = elem.text.strip()
                        if txt and txt.lower() not in [s.lower() for s in size_names] and txt.lower() != "select":
                            size_names.append(txt)
                    if size_names:
                        break
                return size_names or ["N/A"]
            except Exception:
                return ["N/A"]

        def extract_images():
            image_urls = []
            try:
                thumbs = driver.find_elements(By.CSS_SELECTOR, 'img[data-testid="media-gallery-thumbnail-image"]')
                for thumb in thumbs:
                    try:
                        thumb.click()
                        time.sleep(1)
                        main_img = driver.find_element(By.CSS_SELECTOR, 'img[data-testid="media-gallery-image"]')
                        src = main_img.get_attribute("src")
                        if src and src not in image_urls:
                            image_urls.append(src)
                        if len(image_urls) >= 5:
                            break
                    except Exception:
                        continue
                if not image_urls:
                    fallback_imgs = driver.find_elements(By.CSS_SELECTOR, 'img')
                    for img in fallback_imgs:
                        src = img.get_attribute("src")
                        if src and any(ext in src for ext in [".jpg", ".png", ".webp"]) and src not in image_urls:
                            image_urls.append(src)
                        if len(image_urls) >= 5:
                            break
            except Exception:
                pass
            return image_urls

        def extract_about_this_item():
            try:
                desc_elem = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '#product-description-section'))
                )
                paragraphs = desc_elem.find_elements(By.TAG_NAME, 'p')
                lines = [p.text.strip() for p in paragraphs if p.text.strip()]
                return "\n".join(lines) if lines else "N/A"
            except Exception:
                return "N/A"

        def extract_related_links():
            try:
                links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/ip/"]')
                unique_links = list({a.get_attribute("href").split("?")[0] for a in links if a.get_attribute("href")})
                return unique_links
            except Exception:
                return []

        product = {
            "url": url,
            "name": safe_find_text_by_css([
                'h1[data-testid="product-title"]',
                'h1.prod-ProductTitle',
                'h1[itemprop="name"]'
            ], timeout=10),

            "price": safe_find_text_by_css([
                'span[data-testid="price"]',
                'div[data-testid="product-price"] span',
                'span[itemprop="price"]',
                'span.price-characteristic',
                'span.price-group'
            ], timeout=8),

            "images": extract_images(),
            "about_this_item": extract_about_this_item(),
            "colors": extract_colors(),
            "sizes": extract_sizes(),
            "related_links": extract_related_links()
        }

        print("Scraped Data:")
        for k, v in product.items():
            print(f"{k}: {v if isinstance(v, str) else len(v)} items")

        return product

    finally:
        driver.quit()


def scrape_kroger(url):
    return {
        "name": "Kroger Product",
        "price": "2.99",
        "images": [],
        "about_this_item": "Details about Kroger product",
        "colors": ["N/A"],
        "sizes": ["N/A"],
        "url": url,
        "related_links": []
    }


def scrap_url(url):
    if "walmart.com" in url:
        return scrape_walmart(url)
    elif "kroger.com" in url:
        return scrape_kroger(url)
    else:
        raise Exception("Unsupported URL for scraping")
