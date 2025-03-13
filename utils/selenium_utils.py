from typing import List, Optional, Callable
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.options import Options


def initialize_driver(
    headless: bool = True,
    disable_gpu: bool = True,
    no_sandbox: bool = True,
    disable_dev_shm_usage: bool = True,
) -> webdriver.Chrome:
    options = Options()
    options_args = {
        "--headless": headless,
        "--disable-gpu": disable_gpu,
        "--no-sandbox": no_sandbox,
        "--disable-dev-shm-usage": disable_dev_shm_usage,
    }
    for flag, value in options_args.items():
        if value:
            try:
                options.add_argument(flag)
            except:
                pass
    driver = webdriver.Chrome(options=options)
    return driver

def _wait_for_elements(
    driver: webdriver.Chrome,
    by: str = By.ID,
    value: Optional[str] = None,
    timeout: int = 10
) -> None:
    WebDriverWait(driver, timeout).until(
        EC.presence_of_all_elements_located((by, value))
    )

def _try_find_wrapper(
    find_func: Callable[[], WebElement],
    driver: webdriver,
    by: str = By.ID,
    value: Optional[str] = None,
    wait: bool = True,
    timeout: int = 10
):
    try:
        if wait:
            _wait_for_elements(driver, by=by, value=value, timeout=timeout)
        return find_func(by=by, value=value)
    except NoSuchElementException:
        return None

def try_find_element(
    driver: webdriver.Chrome,
    by: str = By.ID,
    value: Optional[str] = None,
    wait: bool = True,
    timeout: int = 10
) -> WebElement:
    return _try_find_wrapper(
        driver.find_element,
        driver,
        value=value,
        by=by,
        wait=wait,
        timeout=timeout
    )

def try_find_elements(
    driver: webdriver.Chrome,
    by: str = By.ID,
    value: Optional[str] = None,
    wait: bool = True,
    timeout: int = 10
) -> WebElement:
    return _try_find_wrapper(
        driver.find_elements,
        driver,
        value=value,
        by=by,
        wait=wait,
        timeout=timeout
    )

def click_element(driver: webdriver.Chrome, elem: WebElement, wait: int = 20, sleep: int = 1):
    WebDriverWait(driver, wait).until(EC.element_to_be_clickable(elem)).click()
    time.sleep(sleep)

def click_element_close_model(driver: webdriver.Chrome, elem: WebElement, wait: int = 20, sleep: int = 1):
    try:
        click_element(driver, elem, sleep=sleep, wait=wait)
    except:
        body = driver.find_element(By.TAG_NAME, "body")
        body.send_keys(Keys.ESCAPE)
        click_element(driver, elem, wait=wait, sleep=sleep)
