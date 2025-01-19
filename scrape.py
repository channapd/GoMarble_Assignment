from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
import uvicorn
import asyncio
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from typing import List, Dict
import os
from dotenv import load_dotenv
import logging
from urllib.parse import urlparse
from selenium.common.exceptions import TimeoutException, NoSuchElementException


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


load_dotenv()


app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    logger.error("OpenAI API key not found in environment variables")
    raise ValueError("OpenAI API key not found")

chat_model = ChatOpenAI(
    model="gpt-4",  
    openai_api_key=openai_api_key,
    temperature=0  
)

class Review(BaseModel):
    title: str
    body: str
    rating: int
    reviewer: str

class ReviewsResponse(BaseModel):
    reviews_count: int
    reviews: List[Review]

def initialize_driver():
    """Initialize Chrome driver with undetected-chromedriver"""
    try:
        options = uc.ChromeOptions()
        options.add_argument('--headless=new')  
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = uc.Chrome(options=options, use_subprocess=True)
        driver.implicitly_wait(10)
        return driver
    except Exception as e:
        logger.error(f"Failed to initialize driver: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize browser: {str(e)}"
        )

async def get_selectors_with_langchain(page_content: str, domain: str) -> Dict[str, str]:
    """Get CSS selectors using LangChain with OpenAI"""
    try:
        
        system_message = SystemMessage(
            content="You are a web scraping expert. Return only CSS selectors."
        )
        user_message = HumanMessage(
            content=f"""
            Analyze this HTML from {domain} and provide CSS and XPath selectors for:
            - Review container
            - Individual review wrapper
            - Review title
            - Review body
            - Rating element
            - Reviewer name
            - Next page button
            
            Return only selectors in format:
            element: selector
            Prefer CSS selectors but use XPath when necessary.
            
            HTML: {page_content[:15000]}
            """
        )

        
        response = await asyncio.to_thread(chat_model, [system_message, user_message])
        selectors = {}

        
        for line in response.content.strip().split('\n'):
            if ':' in line:
                element, selector = line.split(':', 1)
                selectors[element.strip()] = selector.strip()
        return selectors

    except Exception as e:
        logger.error(f"Failed to get selectors with LangChain: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze page structure: {str(e)}"
        )

@app.get("/api/reviews", response_model=ReviewsResponse)
async def get_reviews(page: HttpUrl):
    """Endpoint to scrape reviews from a given URL"""
    logger.info(f"Received request to scrape: {page}")
    driver = None

    try:
        
        driver = initialize_driver()
        wait = WebDriverWait(driver, 10)

        
        logger.info("Navigating to page...")
        driver.get(str(page))

        
        domain = urlparse(str(page)).netloc

        
        content = driver.page_source

        
        logger.info("Getting selectors with LangChain...")
        selectors = await get_selectors_with_langchain(content, domain)

        
        all_reviews = []

        
        logger.info("Starting review extraction...")
        while True:
            try:
                
                container = wait.until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, selectors['Review container'])
                    )
                )

                
                reviews = container.find_elements(
                    By.CSS_SELECTOR,
                    selectors['Individual review wrapper']
                )

                for review in reviews:
                    try:
                        title = review.find_element(
                            By.CSS_SELECTOR,
                            selectors['Review title']
                        )
                        body = review.find_element(
                            By.CSS_SELECTOR,
                            selectors['Review body']
                        )
                        rating = review.find_element(
                            By.CSS_SELECTOR,
                            selectors['Rating element']
                        )
                        reviewer = review.find_element(
                            By.CSS_SELECTOR,
                            selectors['Reviewer name']
                        )

                        
                        try:
                            rating_value = int(float(rating.get_attribute('data-rating')))
                        except:
                            try:
                                rating_value = int(float(rating.get_attribute('content')))
                            except:
                                rating_text = rating.text
                                rating_value = int(float(''.join(filter(str.isdigit, rating_text))))

                        all_reviews.append(Review(
                            title=title.text.strip(),
                            body=body.text.strip(),
                            rating=rating_value,
                            reviewer=reviewer.text.strip()
                        ))
                    except Exception as e:
                        logger.warning(f"Error extracting review: {str(e)}")
                        continue

                
                try:
                    next_button = driver.find_element(
                        By.CSS_SELECTOR,
                        selectors['Next page button']
                    )
                    if next_button.is_displayed() and next_button.is_enabled():
                        driver.execute_script("arguments[0].click();", next_button)
                        wait.until(EC.staleness_of(container))
                    else:
                        break
                except (NoSuchElementException, TimeoutException):
                    break

            except Exception as e:
                logger.warning(f"Error processing page: {str(e)}")
                break

        return ReviewsResponse(
            reviews_count=len(all_reviews),
            reviews=all_reviews
        )

    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    uvicorn.run("scrape:app", host="0.0.0.0", port=8000, reload=True)
