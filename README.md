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
---
Updated the Google Maps Image Scraper to save image URLs to a CSV file in real-time as they're being scraped. Here are the key additions:

## New CSV Features

1. **Real-time URL Saving**: 
   - Each image URL is saved to a CSV file immediately as it's discovered
   - The CSV includes index, URL, and timestamp for each image

2. **Thread-Safe Implementation**:
   - Uses a lock mechanism to prevent issues when multiple threads try to write to the CSV

3. **Organized File Structure**:
   - CSV files are saved in location-specific directories
   - Filenames include location name and timestamp for easy identification

4. **New Command Line Options**:
   - `--no-csv`: Disable saving URLs to CSV
   - `--only-csv`: Only save URLs to CSV without downloading images

## Example Usage

For normal operation with CSV:
```bash
python google_maps_image_scraper.py "Empire State Building"
```

To only save URLs without downloading images:
```bash
python google_maps_image_scraper.py "Empire State Building" --only-csv
```

To disable CSV saving:
```bash
python google_maps_image_scraper.py "Empire State Building" --no-csv
```

## CSV File Format

The CSV file includes three columns:
1. **index**: Sequential number for each image
2. **image_url**: Full URL to the high-resolution image
3. **timestamp**: When the URL was discovered

This implementation allows you to have a complete record of all image URLs, which can be useful for:
- Resuming downloads later
- Sharing URL lists with others
- Processing URLs with external tools
- Keeping a record of available images even if you choose not to download them

The CSV is created at the start of scraping and updated in real-time as each new URL is discovered, so you'll have the data even if the script is interrupted.
