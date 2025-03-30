# Google SERP API

Simple API for scraping Google search results using headless Chrome.

## Features

- Google search results scraping with anti-bot protection bypass
- Support for multiple search parameters
- Proxy support
- Headless Chrome automation

## API Endpoints

### GET /search

Returns Google search results as JSON.

**Parameters:**

| Parameter | Type   | Description                      | Example          |
|-----------|--------|----------------------------------|------------------|
| query     | string | Search query (required)          | pizza            |
| domain    | string | Google domain                    | google.com       |
| num       | int    | Number of results (10-100)       | 10               |
| gl        | string | Geolocation parameter            | us               |
| hl        | string | Interface language               | en               |
| lr        | string | Results language                 | lang_en          |
| cr        | string | Country restriction              | countryUS        |
| location  | string | Location for geo-targeted results| New York,US      |

### GET /counter

Returns the total number of successful requests made to the API.

## Sample Usage

### Python Example

```python
import requests

# API endpoint
url = "http://your-server:8000/search"

# Parameters
params = {
    "query": "pizza delivery",
    "domain": "google.com",
    "num": 10,
    "gl": "us",
    "hl": "en"
}

# Make request
response = requests.get(url, params=params)

# Parse results
if response.status_code == 200:
    results = response.json()
    print(f"Found {results['organic_count']} organic results")
    
    # Access organic results
    for result in results['parsed_data']['organic']:
        print(f"Title: {result['title']}")
        print(f"URL: {result['url']}")
        print("---")
```

## Deployment

Built with Docker for easy deployment:

```bash
docker compose up -d
``` 