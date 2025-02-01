import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def click_button_if_exists(url):
    options = Options()
    options.add_argument('--headless')  # Run headless for minimal resource usage
    options.add_argument('--disable-gpu')  # Optional, for environments with no GPU
    options.add_argument('--no-sandbox')  # Optional, helpful in some environments
    options.add_argument('--disable-dev-shm-usage')  # Optional, for better performance
    
    # Set up Chrome WebDriver
    driver = webdriver.Chrome(options=options)
    
    # Open the URL
    driver.get(url)

    try:
        # Wait until at least one button is present on the page (timeout after 10 seconds)
        print("\t...Loading elements")
        st = time.time()
        buttons = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "button"))
        )
        end = time.time()
        print(f"\t......All elements loaded ({end - st} sec)")
        print(f"\t...Buttons found: {len(buttons)}")
        if len(buttons) == 1:
            button = buttons[0]
            data_testid = button.get_attribute("data-testid")
            print(f"\t...Button's 'data-testid': {data_testid}")
            if data_testid and isinstance(data_testid, str) and "wake" in data_testid:
                print("\t...Clicking button")
                button.click()
                time.sleep(1)
                button.click()
                time.sleep(1)
                button.click()
                time.sleep(1)
                button.click()
                time.sleep(1)
                print("\t.....Button clicked!")
    except Exception as e:
        print("\tButton not found or an error occurred:", e)
    finally:
        driver.quit()

# Example usage
if __name__ == "__main__":
    streamlit_apps = {
        "Portfolio Optimization App": "https://stocks-portfolio-optimization.streamlit.app/",
        "NJ Programs Bot": "https://nj-programs-bot.streamlit.app/"
    }
    for i, (app_name, url) in enumerate(streamlit_apps.items()):
        print(f"{i + 1} / {len(streamlit_apps)}: Waking up '{app_name}'...")
        click_button_if_exists(url)
