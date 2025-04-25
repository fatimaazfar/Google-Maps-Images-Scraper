import os
import time
import logging
import argparse
import requests
import csv
import threading
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    ElementClickInterceptedException,
    StaleElementReferenceException,
    WebDriverException
)
from webdriver_manager.chrome import ChromeDriverManager
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse, unquote
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("gmaps_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def create_csv_file(self, location_name):
        """
        Create a CSV file for storing image URLs
        
        Args:
            location_name (str): Name of the location
            
        Returns:
            str: Path to the created CSV file
        """
        location_dir = os.path.join(self.download_dir, self._sanitize_filename(location_name))
        if not os.path.exists(location_dir):
            os.makedirs(location_dir)
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"{self._sanitize_filename(location_name)}_urls_{timestamp}.csv"
        csv_path = os.path.join(location_dir, csv_filename)
        
        # Create the CSV file with headers
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(['index', 'image_url', 'timestamp'])
            
        logger.info(f"Created CSV file: {csv_path}")
        return csv_path
        
def save_url_to_csv(self, csv_path, url, index):
    """
    Save a URL to the CSV file in a thread-safe manner
    
    Args:
        csv_path (str): Path to the CSV file
        url (str): Image URL to save
        index (int): Index of the URL
        
    Returns:
        bool: True if saved successfully, False otherwise
    """
    try:
        with self.csv_lock:  # Use lock to prevent multiple threads from writing simultaneously
            with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
                csv_writer = csv.writer(csvfile)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                csv_writer.writerow([index, url, timestamp])
                
                # Flush after each write to ensure real-time updates
                csvfile.flush()
                
                # Log every 10th URL or first few URLs
                if index <= 5 or index % 10 == 0:
                    print(f"Saved URL #{index} to CSV")
                    logger.info(f"Saved URL #{index} to CSV: {url[:50]}...")
        return True
    except Exception as e:
        logger.error(f"Error saving URL to CSV: {str(e)}")
        return False
    
class GoogleMapsImageScraper:
    def __init__(self, headless=True, download_dir="downloaded_images", timeout=30, save_csv=True):
        """
        Initialize the Google Maps Image Scraper
        
        Args:
            headless (bool): Run browser in headless mode
            download_dir (str): Directory to save downloaded images
            timeout (int): Default timeout for WebDriverWait
            save_csv (bool): Whether to save image URLs to CSV
        """
        self.download_dir = download_dir
        self.timeout = timeout
        self.save_csv = save_csv
        self.csv_lock = threading.Lock()  # Lock for thread-safe CSV operations
        
        # Create download directory if it doesn't exist
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
            
        # Setup Chrome options
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Enable user agent to avoid detection
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        # Initialize WebDriver with Chrome
        try:
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            self.driver.maximize_window()
            logger.info("WebDriver initialized successfully")
        except WebDriverException as e:
            logger.error(f"Failed to initialize WebDriver: {str(e)}")
            raise
            
    def create_csv_file(self, location_name):
        """
        Create a CSV file for storing image URLs
        
        Args:
            location_name (str): Name of the location
            
        Returns:
            str: Path to the created CSV file
        """
        location_dir = os.path.join(self.download_dir, self._sanitize_filename(location_name))
        if not os.path.exists(location_dir):
            os.makedirs(location_dir)
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"{self._sanitize_filename(location_name)}_urls_{timestamp}.csv"
        csv_path = os.path.join(location_dir, csv_filename)
        
        # Create the CSV file with headers
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(['index', 'image_url', 'timestamp'])
            
        logger.info(f"Created CSV file: {csv_path}")
        return csv_path
        
    def save_url_to_csv(self, csv_path, url, index):
        """
        Save a URL to the CSV file in a thread-safe manner
        
        Args:
            csv_path (str): Path to the CSV file
            url (str): Image URL to save
            index (int): Index of the URL
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            with self.csv_lock:  # Use lock to prevent multiple threads from writing simultaneously
                with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
                    csv_writer = csv.writer(csvfile)
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    csv_writer.writerow([index, url, timestamp])
                    
                    # Flush after each write to ensure real-time updates
                    csvfile.flush()
                    
                    # Log every 10th URL or first few URLs
                    if index <= 5 or index % 10 == 0:
                        print(f"Saved URL #{index} to CSV")
                        logger.info(f"Saved URL #{index} to CSV: {url[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Error saving URL to CSV: {str(e)}")
            return False
            
    def _is_in_gallery_view(self):
        """
        Check if we're currently in the gallery view
        
        Returns:
            bool: True if we're in gallery view, False otherwise
        """
        try:
            # Check for elements that indicate we're in gallery view
            gallery_indicators = [
                "button[aria-label='Next photo'], button[aria-label='Next']",
                "div.m6QErb.DxyBCb.kA9KIf.dS8AEf",  # Gallery container
                "div.aomaEc, button.aomaEc",  # Next button
                "div.U7izfe",  # Photo view container
                "div.YbQ5dc"   # Another gallery container class
            ]
            
            for indicator in gallery_indicators:
                if len(self.driver.find_elements(By.CSS_SELECTOR, indicator)) > 0:
                    return True
                    
            # Check for JavaScript gallery state
            try:
                in_gallery = self.driver.execute_script("""
                    return (
                        document.querySelector("div[role='dialog'][aria-label*='photo']") !== null ||
                        document.querySelector("div.m6QErb.DxyBCb.kA9KIf.dS8AEf") !== null
                    );
                """)
                
                if in_gallery:
                    return True
            except Exception:
                pass
                
            return False
        except Exception as e:
            logger.debug(f"Error checking gallery view: {str(e)}")
            return False

    def search_location(self, location_name):
        """
        Search for a location on Google Maps
        
        Args:
            location_name (str): Name of the location to search
            
        Returns:
            bool: True if search was successful, False otherwise
        """
        try:
            # Navigate to Google Maps
            self.driver.get("https://www.google.com/maps")
            logger.info(f"Searching for location: {location_name}")
            
            # Add a brief wait for page to load completely
            time.sleep(3)
            
            # Wait for the search box to be present and click on it
            search_box = WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input#searchboxinput, input[name='q'], input[aria-label*='Search']"))
            )
            search_box.clear()
            search_box.send_keys(location_name)
            search_box.send_keys(Keys.ENTER)
            
            # Add delay after search to allow results to load
            time.sleep(3)
            
            # Check if we're directly on the place page (when there's a direct match)
            try:
                # Check if place name is visible in the header/title
                place_header = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h1.DUwDvf, div.fontHeadlineLarge, div[role='heading']"))
                )
                if place_header:
                    logger.info(f"Direct match found: {place_header.text}")
                    return True
            except (TimeoutException, NoSuchElementException):
                pass
                
            # Try to find and click on the first result with multiple approaches
            selectors_to_try = [
                # Current Google Maps selectors
                "div.Nv2PK, div.hfpxzc, a.hfpxzc, div[jsaction*='placecard.card']",
                # Backup selectors
                "div[role='article'], a[jsaction*='placepage'], div.section-result-content",
                # Generic clickable elements containing the location name (case insensitive)
                f"//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{location_name.lower()}')]",
                f"//div[@role='article' and contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{location_name.lower()}')]"
            ]
            
            for selector in selectors_to_try:
                try:
                    if selector.startswith("//"):  # XPath selector
                        element = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:  # CSS selector
                        element = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    # Scroll element into view for better clicking
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                    time.sleep(1)
                    element.click()
                    logger.info(f"Location found and clicked with selector: {selector}")
                    time.sleep(3)  # Wait for place page to load
                    return True
                except (TimeoutException, NoSuchElementException, ElementClickInterceptedException):
                    continue
            
            # If we still haven't found a result, check if we're already on a place page
            # Sometimes Google Maps navigates directly to the place page for exact matches
            try:
                # Check for any place page indicators
                if any([
                    len(self.driver.find_elements(By.CSS_SELECTOR, "button[jsaction*='pane.rating.category']")) > 0,
                    len(self.driver.find_elements(By.CSS_SELECTOR, "button[data-item-id='photos'], button[aria-label*='photo']")) > 0,
                    len(self.driver.find_elements(By.CSS_SELECTOR, "div.RcCsl")) > 0
                ]):
                    logger.info("Already on a place page, continuing...")
                    return True
            except Exception:
                pass
                
            logger.warning(f"No search results found for '{location_name}' after trying all selectors")
            return False
                
        except Exception as e:
            logger.error(f"Error searching for location: {str(e)}")
            return False

    def open_photos_section(self):
        """
        Open the photos section of the location
        
        Returns:
            bool: True if photos section was opened, False otherwise
        """
        try:
            # Add initial delay to ensure page is fully loaded
            time.sleep(3)
            
            # Try multiple approaches to find and click the photos section
            selectors_to_try = [
                # Direct photo buttons
                "button[aria-label*='photo' i], button[data-item-id*='photo' i], a[aria-label*='photo' i], a[data-item-id*='photo' i]",
                # Photo section links
                "a[data-tab='images'], a[data-tab='photos']",
                # Text-based photo buttons
                "//button[.//div[contains(translate(text(), 'PHOTOS', 'photos'), 'photos')]]",
                "//a[.//div[contains(translate(text(), 'PHOTOS', 'photos'), 'photos')]]",
                # Photo icon buttons
                "button[jsaction*='photo'], button[jsaction*='image']",
                # Photo count elements
                "span.YbCJSd, div.bJP2oh, div.Yr7JMd",
                # Photo thumbnails directly
                "div.U39Pmb img, div.AdyRSe"
            ]
            
            for selector in selectors_to_try:
                try:
                    # Check if we need to use XPath
                    if selector.startswith("//"):
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        
                    if elements:
                        # Try clicking the first element that's visible and enabled
                        for element in elements:
                            if element.is_displayed():
                                # Scroll element into view
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                                time.sleep(1)
                                
                                # Try direct click
                                try:
                                    element.click()
                                    logger.info(f"Photos section opened using selector: {selector}")
                                    time.sleep(3)  # Wait for photos to load
                                    return True
                                except ElementClickInterceptedException:
                                    # Try JavaScript click if direct click fails
                                    try:
                                        self.driver.execute_script("arguments[0].click();", element)
                                        logger.info(f"Photos section opened using JavaScript click with selector: {selector}")
                                        time.sleep(3)
                                        return True
                                    except Exception:
                                        continue
                except Exception as e:
                    logger.debug(f"Failed with selector {selector}: {str(e)}")
                    continue
            
            # Check if we're already in the photos section
            try:
                photo_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.loaded-media-item-container, div[role='img'], img.qaFoQ, div.gallery-image-high-res")
                if len(photo_elements) > 0:
                    logger.info("Already in photos section")
                    return True
            except Exception:
                pass
                
            logger.error("Could not open photos section after trying all selectors")
            return False
            
        except Exception as e:
            logger.error(f"Error opening photos section: {str(e)}")
            return False

    def extract_image_urls(self, max_images=None, location_name=None):
        """
        Extract all image URLs from the photos section
        
        Args:
            max_images (int, optional): Maximum number of images to extract
            location_name (str, optional): Name of the location for CSV
            
        Returns:
            list: List of image URLs
        """
        image_urls = set()
        last_count = 0
        scroll_attempts = 0
        max_scroll_attempts = 30
        retry_attempts = 3
        
        # Set up CSV if needed
        csv_path = None
        if self.save_csv and location_name:
            csv_path = self.create_csv_file(location_name)
            print(f"Creating CSV file at: {csv_path}")
            logger.info(f"Creating CSV file at: {csv_path}")
        
        logger.info("Starting to extract image URLs")
        
        # First check if we need to click on an image to open the gallery
        gallery_attempt = 0
        while not self._is_in_gallery_view() and gallery_attempt < retry_attempts:
            try:
                gallery_attempt += 1
                logger.info(f"Attempting to enter gallery view (attempt {gallery_attempt}/{retry_attempts})")
                
                # Try various selectors for the first image
                selectors_to_try = [
                    "div[role='img'], img.qaFoQ",
                    "div.loaded-media-item-container img",
                    "div.gallery-image-container img",
                    "img.qTegM, img.r7MLu, img.OVwCQd",
                    "div.AdyRSe, div.U39Pmb",
                    # Generic image elements that might be part of the gallery
                    "div.photos-album-container img",
                    "img[src*='googleusercontent']"
                ]
                
                for selector in selectors_to_try:
                    try:
                        elements = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                        )
                        
                        if elements:
                            for element in elements:
                                if not element.is_displayed():
                                    continue
                                    
                                # Scroll into view and click
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                                time.sleep(2)  # Increased wait time
                                
                                try:
                                    # Try a fresh reference to the element to avoid stale references
                                    # Re-find the element after scrolling
                                    elements_after_scroll = self.driver.find_elements(By.CSS_SELECTOR, selector)
                                    for el in elements_after_scroll:
                                        if el.is_displayed():
                                            el.click()
                                            logger.info(f"Image clicked to open gallery view using selector: {selector}")
                                            time.sleep(3)  # Wait for gallery to load
                                            break
                                except Exception as e:
                                    logger.debug(f"Direct click failed: {str(e)}")
                                    # Try JavaScript click if direct click fails
                                    try:
                                        self.driver.execute_script("arguments[0].click();", element)
                                        logger.info("Image clicked with JavaScript to open gallery view")
                                        time.sleep(3)
                                        break
                                    except Exception as js_e:
                                        logger.debug(f"JavaScript click failed: {str(js_e)}")
                                        continue
                            
                            # Check if we're now in gallery view
                            if self._is_in_gallery_view():
                                break
                    except Exception as e:
                        logger.debug(f"Error with selector {selector}: {str(e)}")
                        continue
                
                # If we've entered gallery view, break out of retry loop
                if self._is_in_gallery_view():
                    break
                    
                # If not in gallery view after trying all selectors, retry a different approach
                if gallery_attempt < retry_attempts:
                    logger.info(f"Could not enter gallery view, trying alternative approach...")
                    
                    # Try clicking on the "Photos" text link if available
                    try:
                        photo_links = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'Photos')] | //span[contains(text(), 'Photos')]")
                        if photo_links:
                            for link in photo_links:
                                if link.is_displayed():
                                    self.driver.execute_script("arguments[0].click();", link)
                                    time.sleep(3)
                                    break
                    except Exception:
                        pass
                    
                    # Try to refresh the page and wait before next attempt
                    try:
                        self.driver.refresh()
                        time.sleep(5)
                    except Exception:
                        pass
                
            except Exception as e:
                logger.warning(f"Error attempting to enter gallery view (attempt {gallery_attempt}): {str(e)}")
                time.sleep(2)
        
        # If we still aren't in gallery view after all retries, use an alternative approach
        if not self._is_in_gallery_view():
            logger.warning("Could not enter gallery view, attempting to extract images directly")
            direct_urls = self._extract_images_direct()
            
            # Save direct URLs to CSV if needed
            if csv_path and direct_urls:
                for i, url in enumerate(direct_urls):
                    self.save_url_to_csv(csv_path, url, i+1)
                    
            return direct_urls
        
        logger.info("Successfully entered gallery view, beginning image extraction")
        
        # Extract images by navigating through the gallery
        consecutive_errors = 0
        max_consecutive_errors = 5
        url_index = 1  # Counter for URLs found
        
        while True:
            try:
                # Try multiple selectors for the current image
                img_selectors = [
                    "img.aIMqZ, div.OhtVzd img",
                    "div.YmEk1d img, img.tK6ULc",
                    "div[role='main'] img[src*='googleusercontent']",
                    "div.gallery-image-high-res img",
                    "img[style*='transform']",  # Often the main image has transform styles
                    "div.gallery-image-container img"
                ]
                
                found_image = False
                for selector in img_selectors:
                    try:
                        # Use WebDriverWait to ensure elements are present
                        wait = WebDriverWait(self.driver, 5)
                        img_elements = wait.until(
                            EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                        )
                        
                        for img_element in img_elements:
                            if not img_element.is_displayed():
                                continue
                                
                            # Get image URL with retry for stale references
                            for retry in range(3):
                                try:
                                    current_url = img_element.get_attribute("src")
                                    break
                                except StaleElementReferenceException:
                                    if retry < 2:  # Last retry
                                        logger.debug(f"Stale reference when getting src, retry {retry+1}/3")
                                        # Re-find element
                                        wait = WebDriverWait(self.driver, 5)
                                        img_elements = wait.until(
                                            EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                                        )
                                        if img_elements:
                                            img_element = img_elements[0]
                                        time.sleep(1)
                                    else:
                                        current_url = None
                                except Exception:
                                    current_url = None
                                    break
                            
                            # Add high-resolution version of image URL
                            if current_url and "googleusercontent.com" in current_url:
                                # Transform URL to get the highest resolution
                                high_res_url = re.sub(r'=w\d+-h\d+', '=w0-h0', current_url)
                                
                                # Only add if it's a new URL
                                if high_res_url not in image_urls:
                                    image_urls.add(high_res_url)
                                    logger.debug(f"Added image URL: {high_res_url}")
                                    
                                    # Save URL to CSV in real-time
                                    if csv_path:
                                        self.save_url_to_csv(csv_path, high_res_url, url_index)
                                        url_index += 1
                                        
                                found_image = True
                                consecutive_errors = 0  # Reset error counter on success
                                break
                    except Exception as e:
                        logger.debug(f"Error with image selector {selector}: {str(e)}")
                        continue
                        
                if not found_image:
                    # Try JavaScript approach if no images found with regular selectors
                    try:
                        # Get all images from the page using JavaScript
                        all_imgs = self.driver.execute_script("""
                            return Array.from(document.querySelectorAll('img'))
                                .filter(img => img.src && img.src.includes('googleusercontent'))
                                .map(img => img.src);
                        """)
                        
                        for url in all_imgs:
                            if "googleusercontent.com" in url:
                                high_res_url = re.sub(r'=w\d+-h\d+', '=w0-h0', url)
                                
                                # Only add if it's a new URL
                                if high_res_url not in image_urls:
                                    image_urls.add(high_res_url)
                                    
                                    # Save URL to CSV in real-time
                                    if csv_path:
                                        self.save_url_to_csv(csv_path, high_res_url, url_index)
                                        url_index += 1
                                        
                                found_image = True
                                consecutive_errors = 0  # Reset error counter on success
                    except Exception as e:
                        logger.debug(f"JavaScript image extraction failed: {str(e)}")
                
                if not found_image:
                    consecutive_errors += 1
                    logger.warning(f"No image found on this page (consecutive errors: {consecutive_errors}/{max_consecutive_errors})")
                    if consecutive_errors >= max_consecutive_errors:
                        logger.warning("Too many consecutive errors, stopping extraction")
                        break
                
                # Check if we've reached the max number of images
                if max_images and len(image_urls) >= max_images:
                    logger.info(f"Reached maximum number of images: {max_images}")
                    break
                
                # Try different selectors for the next button
                next_button_selectors = [
                    "button[aria-label='Next photo'], button[aria-label='Next']",
                    "[jsaction*='pane.nextbatch']",
                    "button.mL3Fgc, button[aria-label*='next']",
                    "button.tit8B, button.aomaEc",
                    "//button[contains(@aria-label, 'Next')]"  # XPath for "Next" in various languages
                ]
                
                next_clicked = False
                for selector in next_button_selectors:
                    try:
                        if selector.startswith("//"):  # XPath selector
                            next_buttons = WebDriverWait(self.driver, 5).until(
                                EC.presence_of_all_elements_located((By.XPATH, selector))
                            )
                        else:  # CSS selector
                            next_buttons = WebDriverWait(self.driver, 5).until(
                                EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                            )
                            
                        if next_buttons:
                            for btn in next_buttons:
                                if not btn.is_displayed():
                                    continue
                                
                                try:
                                    # Scroll button into view first
                                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                                    time.sleep(1)
                                    
                                    # Try to click with fresh reference after scrolling
                                    if selector.startswith("//"):
                                        refreshed_buttons = self.driver.find_elements(By.XPATH, selector)
                                    else:
                                        refreshed_buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                                    
                                    for refreshed_btn in refreshed_buttons:
                                        if refreshed_btn.is_displayed():
                                            refreshed_btn.click()
                                            next_clicked = True
                                            time.sleep(2)  # Increased wait time
                                            break
                                except ElementClickInterceptedException:
                                    # Try JavaScript click
                                    self.driver.execute_script("arguments[0].click();", btn)
                                    next_clicked = True
                                    time.sleep(2)
                                    break
                                except StaleElementReferenceException:
                                    logger.debug("Stale element when clicking next, retrying with fresh elements")
                                    continue
                        
                        if next_clicked:
                            break
                    except Exception as e:
                        logger.debug(f"Error with next button selector {selector}: {str(e)}")
                        continue
                
                if not next_clicked:
                    logger.info("Could not find or click next button, assuming end of gallery")
                    break
                
                # Check if we're still finding new images
                if len(image_urls) == last_count:
                    scroll_attempts += 1
                else:
                    scroll_attempts = 0
                    
                last_count = len(image_urls)
                
                # If we're not finding new images after multiple attempts, we've likely reached the end
                if scroll_attempts >= max_scroll_attempts:
                    logger.info("No new images found after multiple attempts, stopping extraction")
                    break
                    
            except StaleElementReferenceException:
                logger.warning("Stale element reference, retrying...")
                consecutive_errors += 1
                time.sleep(2)
                if consecutive_errors >= max_consecutive_errors:
                    logger.warning("Too many consecutive stale element errors, stopping extraction")
                    break
            except Exception as e:
                logger.error(f"Unexpected error during image extraction: {str(e)}")
                consecutive_errors += 1
                time.sleep(2)
                if consecutive_errors >= max_consecutive_errors:
                    logger.warning("Too many consecutive errors, stopping extraction")
                    break
                
        logger.info(f"Extracted {len(image_urls)} unique image URLs")
        
        if csv_path:
            logger.info(f"Image URLs saved to: {csv_path}")
            
        return list(image_urls)
        
    def _extract_images_direct(self, csv_path=None):
        """
        Alternative method to extract images directly from the page without gallery navigation
        
        Args:
            csv_path (str, optional): Path to CSV file to save URLs
            
        Returns:
            list: List of image URLs
        """
        image_urls = set()
        url_index = 1  # For CSV indexing
        logger.info("Attempting to extract images directly from the page")
        
        try:
            # First try to get all images with src containing googleusercontent
            js_images = self.driver.execute_script("""
                return Array.from(document.querySelectorAll('img'))
                    .filter(img => img.src && img.src.includes('googleusercontent'))
                    .map(img => img.src);
            """)
            
            for url in js_images:
                if "googleusercontent.com" in url:
                    high_res_url = re.sub(r'=w\d+-h\d+', '=w0-h0', url)
                    image_urls.add(high_res_url)
                    
                    # Save to CSV if needed
                    if csv_path:
                        self.save_url_to_csv(csv_path, high_res_url, url_index)
                        url_index += 1
            
            logger.info(f"Found {len(image_urls)} images using JavaScript extraction")
            
            # If JavaScript approach didn't find enough images, try selectors
            if len(image_urls) < 5:
                image_selectors = [
                    "img[src*='googleusercontent']",
                    "div.section-image-container img",
                    "div.photos-album-container img",
                    "img.qaFoQ"
                ]
                
                for selector in image_selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            try:
                                if element.is_displayed():
                                    url = element.get_attribute("src")
                                    if url and "googleusercontent.com" in url:
                                        high_res_url = re.sub(r'=w\d+-h\d+', '=w0-h0', url)
                                        if high_res_url not in image_urls:
                                            image_urls.add(high_res_url)
                                            
                                            # Save to CSV if needed
                                            if csv_path:
                                                self.save_url_to_csv(csv_path, high_res_url, url_index)
                                                url_index += 1
                            except StaleElementReferenceException:
                                continue
                    except Exception:
                        continue
            
            logger.info(f"Extracted {len(image_urls)} unique image URLs directly from page")
            
        except Exception as e:
            logger.error(f"Error during direct image extraction: {str(e)}")
            
        return list(image_urls)

    def download_image(self, url, location_name, index):
        """
        Download an image from a URL
        
        Args:
            url (str): URL of the image
            location_name (str): Name of the location for the filename
            index (int): Index of the image for the filename
            
        Returns:
            bool: True if download was successful, False otherwise
        """
        try:
            # Create location-specific directory
            location_dir = os.path.join(self.download_dir, self._sanitize_filename(location_name))
            if not os.path.exists(location_dir):
                os.makedirs(location_dir)
                
            # Extract file extension from URL or default to .jpg
            parsed_url = urlparse(url)
            path = unquote(parsed_url.path)
            ext = os.path.splitext(path)[1]
            if not ext or ext == '.':
                ext = '.jpg'
                
            # Create filename
            filename = f"{self._sanitize_filename(location_name)}_{index}{ext}"
            filepath = os.path.join(location_dir, filename)
            
            # Log download attempt
            logger.debug(f"Attempting to download: {url[:50]}... to {filepath}")
            
            # Download the image with timeout and headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://www.google.com/maps'
            }
            
            # Use requests with retry mechanism
            max_retries = 3
            for retry in range(max_retries):
                try:
                    response = requests.get(url, headers=headers, timeout=30)
                    response.raise_for_status()
                    break
                except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
                    if retry < max_retries - 1:
                        logger.warning(f"Retry {retry+1}/{max_retries} for image {index}: {str(e)}")
                        time.sleep(2)  # Wait before retry
                    else:
                        raise
            
            # If file exists, don't overwrite
            if os.path.exists(filepath):
                logger.info(f"File already exists, skipping: {filename}")
                return True
                
            # Save the image
            with open(filepath, 'wb') as f:
                f.write(response.content)
                
            # Check if file was created successfully
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                logger.info(f"Successfully downloaded: {filename}")
                # Print first few and periodic updates
                if index <= 5 or index % 10 == 0:
                    print(f"Downloaded image #{index}: {filename}")
                return True
            else:
                logger.error(f"File was not created or is empty: {filepath}")
                return False
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading image {index}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error downloading image {index}: {str(e)}")
            return False

    def download_all_images(self, image_urls, location_name, max_workers=5):
        """
        Download all images using multiple threads
        
        Args:
            image_urls (list): List of image URLs
            location_name (str): Name of the location
            max_workers (int): Maximum number of worker threads
            
        Returns:
            int: Number of successfully downloaded images
        """
        if not image_urls:
            logger.warning("No image URLs to download")
            return 0
            
        logger.info(f"Starting download of {len(image_urls)} images with {max_workers} workers")
        print(f"Starting download of {len(image_urls)} images with {max_workers} workers")
        
        successful_downloads = 0
        
        # Use ThreadPoolExecutor for parallel downloads
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for i, url in enumerate(image_urls):
                futures.append(executor.submit(self.download_image, url, location_name, i+1))
                
            # Collect results with progress updates
            for i, future in enumerate(futures):
                if future.result():
                    successful_downloads += 1
                
                # Print progress
                if (i+1) % 5 == 0 or i+1 == len(futures):
                    print(f"Downloaded {successful_downloads}/{i+1} images...")
                    
        logger.info(f"Successfully downloaded {successful_downloads} out of {len(image_urls)} images")
        print(f"Successfully downloaded {successful_downloads} out of {len(image_urls)} images")
        return successful_downloads

    def _sanitize_filename(self, filename):
        """
        Sanitize a string to be used as a filename
        
        Args:
            filename (str): String to sanitize
            
        Returns:
            str: Sanitized string
        """
        # Replace invalid characters with underscore
        sanitized = re.sub(r'[\\/*?:"<>|]', '_', filename)
        # Remove leading/trailing whitespace and periods
        sanitized = sanitized.strip('. ')
        # Replace multiple spaces with single underscore
        sanitized = re.sub(r'\s+', '_', sanitized)
        return sanitized

    def close(self):
        """Close the WebDriver"""
        if hasattr(self, 'driver'):
            try:
                self.driver.quit()
                logger.info("WebDriver closed successfully")
            except Exception as e:
                logger.error(f"Error closing WebDriver: {str(e)}")

    def scrape_location_images(self, location_name, max_images=None, max_workers=5):
        """
        Main method to scrape images for a location
        
        Args:
            location_name (str): Name of the location to search
            max_images (int, optional): Maximum number of images to extract
            max_workers (int): Maximum number of worker threads for downloading
            
        Returns:
            tuple: (success status, number of images downloaded)
        """
        try:
            # Search for the location
            if not self.search_location(location_name):
                logger.error(f"Failed to find location: {location_name}")
                return False, 0
                
            # Wait for the location page to load
            time.sleep(3)
            
            # Open photos section
            if not self.open_photos_section():
                logger.error(f"Failed to open photos section for: {location_name}")
                return False, 0
                
            # Extract image URLs
            image_urls = self.extract_image_urls(max_images, location_name)
            if not image_urls:
                logger.warning(f"No images found for: {location_name}")
                return True, 0
                
            # If in --only-csv mode, skip downloading
            if max_workers == 0:
                logger.info(f"Skipping download as --only-csv mode is enabled. Found {len(image_urls)} image URLs.")
                print(f"Found {len(image_urls)} image URLs for: {location_name}")
                print(f"URLs saved to CSV. Skipping download as --only-csv mode is enabled.")
                return True, len(image_urls)
                
            # Download images
            downloaded_count = self.download_all_images(image_urls, location_name, max_workers)
            
            return True, downloaded_count
            
        except Exception as e:
            logger.error(f"Error during scraping process: {str(e)}")
            return False, 0
        finally:
            # Close the browser
            self.close()


def main():
    """Main function to run the scraper from command line"""
    parser = argparse.ArgumentParser(description='Google Maps Image Scraper')
    parser.add_argument('location', type=str, help='Location name to search for')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    parser.add_argument('--download-dir', type=str, default='downloaded_images', help='Directory to save downloaded images')
    parser.add_argument('--max-images', type=int, default=None, help='Maximum number of images to download')
    parser.add_argument('--max-workers', type=int, default=5, help='Maximum number of worker threads for downloading')
    parser.add_argument('--timeout', type=int, default=30, help='Timeout in seconds for WebDriverWait')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode with more detailed logs')
    parser.add_argument('--no-headless', action='store_true', help='Force browser to run in visible mode (overrides --headless)')
    parser.add_argument('--retry-attempts', type=int, default=3, help='Number of retry attempts for each step')
    parser.add_argument('--no-csv', action='store_true', help='Disable saving URLs to CSV file')
    parser.add_argument('--only-csv', action='store_true', help='Only save URLs to CSV, don\'t download images')
    
    args = parser.parse_args()
    
    # Configure logging level based on debug flag
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.info("Debug mode enabled")
    
    # Determine headless mode
    use_headless = args.headless and not args.no_headless
    
    try:
        print(f"Initializing scraper for: {args.location}")
        print(f"Browser mode: {'Headless' if use_headless else 'Visible'}")
        print(f"CSV mode: {'Disabled' if args.no_csv else 'Enabled'}")
        
        # Initialize scraper
        scraper = GoogleMapsImageScraper(
            headless=use_headless,
            download_dir=args.download_dir,
            timeout=args.timeout,
            save_csv=not args.no_csv
        )
        
        # Run scraper with retry logic
        success = False
        downloaded_count = 0
        attempts = 0
        
        while not success and attempts < args.retry_attempts:
            if attempts > 0:
                print(f"Retry attempt {attempts}/{args.retry_attempts}...")
                
            success, downloaded_count = scraper.scrape_location_images(
                args.location,
                max_images=args.max_images,
                max_workers=0 if args.only_csv else args.max_workers  # Don't download if only-csv mode
            )
            
            if success and (downloaded_count > 0 or args.only_csv):
                break
                
            attempts += 1
            if attempts < args.retry_attempts and not success:
                print("Retrying in 3 seconds...")
                time.sleep(3)
                
                # Reinitialize scraper for next attempt
                scraper = GoogleMapsImageScraper(
                    headless=use_headless,
                    download_dir=args.download_dir,
                    timeout=args.timeout,
                    save_csv=not args.no_csv
                )
        
        # Print result
        location_dir = os.path.abspath(os.path.join(args.download_dir, scraper._sanitize_filename(args.location)))
        
        if success:
            if args.only_csv:
                # In CSV-only mode, look for the CSV file to report success
                csv_files = [f for f in os.listdir(location_dir) if f.endswith('.csv')] if os.path.exists(location_dir) else []
                if csv_files:
                    csv_path = os.path.join(location_dir, csv_files[0])
                    # Count lines in CSV (minus header)
                    with open(csv_path, 'r', encoding='utf-8') as f:
                        url_count = sum(1 for _ in f) - 1  # Subtract 1 for header
                    print(f"Scraping completed successfully. Saved {url_count} image URLs to CSV.")
                    print(f"CSV file saved to: {csv_path}")
                else:
                    print(f"Scraping completed, but no CSV file was created.")
            else:
                print(f"Scraping completed successfully. Downloaded {downloaded_count} images.")
                if not args.no_csv:
                    csv_files = [f for f in os.listdir(location_dir) if f.endswith('.csv')] if os.path.exists(location_dir) else []
                    if csv_files:
                        print(f"Image URLs also saved to: {os.path.join(location_dir, csv_files[0])}")
                print(f"Images saved to: {location_dir}")
            return 0
        else:
            if success:
                print(f"Scraping completed, but no images were found for: {args.location}")
            else:
                print(f"Scraping failed after {args.retry_attempts} attempts. Check logs for details.")
            return 1
            
    except KeyboardInterrupt:
        print("\nScraping interrupted by user.")
        return 1
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        logger.exception("Unhandled exception in main")
        return 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)