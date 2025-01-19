# GoMarble_Assignment

An intelligent web scraping API that uses GPT-4 to dynamically determine selectors and extract reviews from any review website. The system combines FastAPI, Selenium with undetected-chromedriver, and LangChain to create a robust and adaptable scraping solution.

Solution Approach
The API implements a multi-step process to extract reviews:

Browser Initialization

1) Uses undetected-chromedriver to bypass anti-bot measures

2) Runs Chrome in headless mode for efficiency

3)Implements proper error handling and resource cleanup


Dynamic Selector Generation

1) Leverages GPT-4 through LangChain to analyze page structure
2) Automatically determines appropriate CSS/XPath selectors
3) Adapts to different website layouts without manual configuration


Review Extraction

1) Implements pagination handling for complete data collection
2) Extracts structured data including title, body, rating, and reviewer
3) Includes robust error handling for individual review extraction
4) Handles various rating formats and normalizes the data
