from io import BytesIO
from time import sleep
import helium
from dotenv import load_dotenv
from PIL import Image
from selenium import webdriver
from selenium.common.exceptions import ElementNotInteractableException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from smolagents import CodeAgent, LiteLLMModel, tool
from smolagents.agents import ActionStep

# Load environment variables
load_dotenv()
import os

########################################
# 1. SET UP THE MODEL
########################################
model = LiteLLMModel(
    model_id="gpt-4o",
    api_key=os.getenv("OPENAI_API_KEY"),
)

########################################
# 2. SCREENSHOT CALLBACK
########################################
def save_screenshot(step_log: ActionStep, agent: CodeAgent) -> None:
    """
    Captures a screenshot at each step and attaches it to the logs for debugging.

    Args:
        step_log (ActionStep): The current step log.
        agent (CodeAgent): The agent instance.
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
# 3. SELENIUM/HELIUM BROWSER INIT
########################################
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--force-device-scale-factor=1")
chrome_options.add_argument("--window-size=1000,1300")
chrome_options.add_argument("--disable-pdf-viewer")

driver = helium.start_chrome(headless=False, options=chrome_options)

########################################
# 4. TOOLS DEFINITION
########################################

@tool
def navigate_to_zepto() -> str:
    """
    Navigate to the Zepto website and verify page load.

    Returns:
        str: A message indicating success or failure.
    """
    try:
        helium.go_to("https://www.zeptonow.com/")
        helium.wait_until(helium.Text("Search for").exists, timeout_secs=10)
        return "Successfully navigated to Zepto."
    except Exception as e:
        return f"Error navigating to Zepto: {str(e)}"

@tool
def handle_location_popup() -> str:
    """
    Handle Zepto's location popup if it appears.

    Returns:
        str: A message indicating how the location prompt was handled, or if it was not detected.
    """
    try:
        # Sleep briefly to allow the popup to appear
        sleep(2.0)

        # Check for known location button text or selectors
        if helium.Button("Detect my location").exists():
            helium.click(helium.Button("Detect my location"))
            return "Clicked 'Detect my location'."

        if helium.Button("Allow").exists():
            helium.click(helium.Button("Allow"))
            return "Clicked 'Allow' on location popup."

        # Example: If there's a text "Enter your Pin Code"
        if helium.Text("Enter your Pin Code").exists():
            helium.write("400001")  # Example PIN
            helium.click("Confirm")
            return "Entered PIN and confirmed location."

        # If no known popup found, return
        return "No location popup detected."
    except Exception as e:
        return f"Error handling location popup: {str(e)}"

@tool
def search_product(product_name: str) -> str:
    """
    Search for a given product on the Zepto website.

    Args:
        product_name (str): The name of the product to search on website of zepto.

    Returns:
        str: A message indicating success or failure of the search step.
    """
    try:
        helium.click(helium.Link("Search for products"))
        helium.write(product_name)
        helium.press(helium.ENTER)
        helium.wait_until(helium.Text(product_name).exists, timeout_secs=10)
        return f"Successfully searched for '{product_name}'."
    except Exception as e:
        return f"Error searching for '{product_name}': {str(e)}"

@tool
def select_first_product() -> str:
    """
    Select the first product from the search results.

    Returns:
        str: A message about the selection step.
    """
    try:
        helium.wait_until(helium.S(".cursor-pointer").exists, timeout_secs=10)
        helium.click(helium.S(".cursor-pointer"))
        return "Successfully selected the first product."
    except Exception as e:
        return f"Error selecting the first product: {str(e)}"

@tool
def add_to_cart() -> str:
    """
    Add the currently selected product to the cart.

    Returns:
        str: A message indicating success or failure of adding the item to cart.
    """
    try:
        helium.wait_until(helium.Button("Add to Cart").exists, timeout_secs=10)
        helium.click(helium.Button("Add to Cart"))
        return "Successfully added the product to the cart."
    except Exception as e:
        return f"Error adding product to the cart: {str(e)}"

@tool
def close_popups() -> str:
    """
    Close any generic popups or modals visible on the page.

    Returns:
        str: A message indicating popups are closed or an error occurred.
    """
    modal_selectors = [
        "button[class*='close']",
        "[class*='modal']",
        ".modal-close",
        ".close-modal",
    ]
    try:
        wait = WebDriverWait(driver, timeout=1.0)
        for selector in modal_selectors:
            elements = wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
            )
            for element in elements:
                if element.is_displayed():
                    helium.driver.execute_script("arguments[0].click();", element)
        return "Popups closed."
    except Exception as e:
        return f"Error closing popups: {str(e)}"

########################################
# 5. AGENT SETUP
########################################
agent = CodeAgent(
    tools=[
        navigate_to_zepto,
        handle_location_popup,
        search_product,
        select_first_product,
        add_to_cart,
        close_popups,
    ],
    model=model,
    additional_authorized_imports=["helium"],
    step_callbacks=[save_screenshot],
    max_steps=20,
    verbosity_level=2,
)

########################################
# 6. MAIN EXECUTION
########################################
if __name__ == "__main__":
    # Prompt user for product name
    product_name = input("Enter the product you want to search for on Zepto: ")

    # Build the instructions dynamically using the user input
    instructions = f"""
    1. Navigate to the Zepto website.
    2. Handle any location popup that may appear.
    3. Search for '{product_name}'.
    4. Select the first product from the results.
    5. Add the selected product to the cart.
    """

    # Run the agent with these instructions
    result = agent.run(instructions)
    print("\n--- Agent Final Result ---")
    print(result)

