from io import BytesIO
from time import sleep
import helium
from dotenv import load_dotenv
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from smolagents import CodeAgent, LiteLLMModel, tool
from smolagents.agents import ActionStep

# Load .env variables (API keys, etc.)
load_dotenv()
import os

########################################
# 1) MODEL
########################################
model = LiteLLMModel(
    model_id="gpt-4o",
    api_key=os.getenv("OPENAI_API_KEY"),
)

########################################
# 2) SCREENSHOT CALLBACK
########################################
def save_screenshot(step_log: ActionStep, agent: CodeAgent) -> None:
    """
    Captures a screenshot at each step for debugging.
    """
    sleep(1.0)  # Let the page settle
    driver = helium.get_driver()
    if driver:
        png_bytes = driver.get_screenshot_as_png()
        image = Image.open(BytesIO(png_bytes))
        print(f"Captured a screenshot: {image.size} pixels")
        step_log.observations_images = [image.copy()]

    # Attach the current URL
    url_info = f"Current URL: {driver.current_url}"
    if step_log.observations:
        step_log.observations += "\n" + url_info
    else:
        step_log.observations = url_info

########################################
# 3) BROWSER INIT
########################################
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--force-device-scale-factor=1")
chrome_options.add_argument("--window-size=1000,1300")
chrome_options.add_argument("--disable-pdf-viewer")

driver = helium.start_chrome(headless=False, options=chrome_options)

########################################
# 4) TOOLS
########################################

@tool
def navigate_to_zepto() -> str:
    """
    Navigate to the Zepto homepage.
    
    Returns:
        str: Success or error message.
    """
    try:
        helium.go_to("https://www.zeptonow.com/")
        helium.wait_until(helium.Text("Search for").exists, timeout_secs=10)
        return "Successfully navigated to Zepto."
    except Exception as e:
        return f"Error navigating to Zepto: {str(e)}"

@tool
def scrape_categories() -> str:
    """
    Scrapes category names from the homepage using the provided HTML snippet.
    
    Returns:
        str: Comma-separated category names or an error message.
    """
    try:
        # Wait until at least one category element is present (2-3 seconds).
        WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[id="CATEGORY_GRID_V3-element"] img[alt]'))
        )

        # Find all <img alt="..."> inside div[id="CATEGORY_GRID_V3-element"]
        category_imgs = driver.find_elements(By.CSS_SELECTOR, 'div[id="CATEGORY_GRID_V3-element"] img[alt]')
        if not category_imgs:
            return "No category images found. Possibly incorrect selector."

        # Collect alt text from each <img>.
        category_names = []
        for img in category_imgs:
            alt_text = img.get_attribute("alt")
            if alt_text:
                category_names.append(alt_text.strip())

        if category_names:
            return f"Categories found: {', '.join(category_names)}"
        else:
            return "No alt text found in category images."
    except Exception as e:
        return f"Error scraping categories: {str(e)}"

########################################
# 5) AGENT
########################################
agent = CodeAgent(
    tools=[navigate_to_zepto, scrape_categories],
    model=model,
    additional_authorized_imports=["helium"],
    step_callbacks=[save_screenshot],
    max_steps=10,
    verbosity_level=2,
)

########################################
# 6) INSTRUCTIONS
########################################
instructions = """
1. Navigate to the Zepto website homepage.
2. Scrape the category names from the homepage using the 'scrape_categories' tool.
3. Return them as final answer.
"""

########################################
# 7) RUN THE AGENT
########################################



if __name__ == "__main__":
    result = agent.run(instructions)
    print("\n--- Agent Final Result ---")
    print(result)
