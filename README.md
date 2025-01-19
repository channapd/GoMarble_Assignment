# GoMarble_Assignment
AI-Powered Review Scraper API
An intelligent web scraping API that uses GPT-4 to dynamically determine selectors and extract reviews from any review website. The system combines FastAPI, Selenium with undetected-chromedriver, and LangChain to create a robust and adaptable scraping solution.
Solution Approach
The API implements a sophisticated multi-step process to extract reviews:

Browser Initialization

Uses undetected-chromedriver to bypass anti-bot measures
Runs Chrome in headless mode for efficiency
Implements proper error handling and resource cleanup


Dynamic Selector Generation

Leverages GPT-4 through LangChain to analyze page structure
Automatically determines appropriate CSS/XPath selectors
Adapts to different website layouts without manual configuration


Review Extraction

Implements pagination handling for complete data collection
Extracts structured data including title, body, rating, and reviewer
Includes robust error handling for individual review extraction
Handles various rating formats and normalizes the data
