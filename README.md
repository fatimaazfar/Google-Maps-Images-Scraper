# Google-Maps-Images-Scraper
A Selenium-based scraper for extracting images from Google Maps location galleries.
Here's how it works:

## Features

- **Location Search**: Automatically searches Google Maps for the specified location
- **Gallery Navigation**: Opens the photos section and navigates through all images
- **High-Resolution Images**: Extracts high-resolution versions of images
- **Parallel Downloads**: Uses multi-threading for efficient downloads
- **Error Handling**: Comprehensive error handling for various failure scenarios
- **Logging**: Detailed logging to track the scraping process

## How to Use

```bash
python google_maps_image_scraper.py "Empire State Building" --max-images 50 --max-workers 5
```

### Command Line Arguments

- `location`: Name of the location to search for (required)
- `--headless`: Run browser in headless mode (optional)
- `--download-dir`: Directory to save images (default: 'downloaded_images')
- `--max-images`: Maximum number of images to download (optional)
- `--max-workers`: Maximum number of threads for downloading (default: 5)
- `--timeout`: Timeout in seconds for WebDriverWait (default: 30)

## Requirements

You'll need to install these dependencies:
```
selenium
webdriver-manager
requests
```
