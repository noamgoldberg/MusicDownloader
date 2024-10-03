from typing import Optional, Callable, List, Union
import time
import os
import stat
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementClickInterceptedException,
    TimeoutException
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType


def get_driver(
    headless: bool = True,
    disable_gpu: bool = True,
    no_sandbox: bool = True,
    disable_dev_shm_usage: bool = True,
) -> webdriver.Chrome:
    options = Options()
    if headless:
        options.add_argument('--headless')
    if disable_gpu:
        options.add_argument('--disable-gpu')
    if no_sandbox:
        options.add_argument('--no-sandbox')
    if disable_dev_shm_usage:
        options.add_argument('--disable-dev-shm-usage')
    chromedriver_install_path = ChromeDriverManager(
        chrome_type=ChromeType.CHROMIUM
    ).install()

    chromedriver_path = str(Path(chromedriver_install_path).parent / "chromedriver")
    
    # Set executable permissions
    os.chmod(chromedriver_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR |  # User
              stat.S_IRGRP | stat.S_IXGRP |                         # Group
              stat.S_IROTH | stat.S_IXOTH)                         # Others
    
    return webdriver.Chrome(service=Service(chromedriver_path), options=options)


def _wait_for_elements(
    driver: webdriver.Chrome,
    by: str = By.ID,
    value: Optional[str] = None,
    timeout: int = 5
) -> List[WebElement]:
    try:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_all_elements_located((by, value))
        )
    except TimeoutException:
        return None

def _try_find_wrapper(
    find_func: Callable[[], WebElement],
    driver: webdriver,
    by: str = By.ID,
    value: Optional[str] = None,
    wait: bool = True,
    timeout: int = 5
) -> Union[WebElement, List[WebElement]]:
    try:
        if wait:
            return _wait_for_elements(driver, by=by, value=value, timeout=timeout)
        return find_func(by=by, value=value)
    except NoSuchElementException:
        return None

def try_find_element(
    driver: webdriver.Chrome,
    by: str = By.ID,
    value: Optional[str] = None,
    wait: bool = True,
    timeout: int = 5
) -> Union[WebElement, None]:
    result = _try_find_wrapper(
        driver.find_element,
        driver,
        value=value,
        by=by,
        wait=wait,
        timeout=timeout
    )
    if isinstance(result, list):
        result = result[0]
    return result or None

def try_find_elements(
    driver: webdriver.Chrome,
    by: str = By.ID,
    value: Optional[str] = None,
    wait: bool = True,
    timeout: int = 5
) -> Union[List[WebElement], None]:
    result = _try_find_wrapper(
        driver.find_elements,
        driver,
        value=value,
        by=by,
        wait=wait,
        timeout=timeout
    )
    return result or None

def click_element(elem: WebElement, sleep: int = 1):
    elem.click()
    time.sleep(sleep)

def click_element_close_model(
    driver: webdriver.Chrome,
    elem: WebElement,
    wait: bool,
    timeout: int = 5,
    sleep: int = 1
):
    if wait:
        elem = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(elem))
    try:
        click_element(elem, sleep)
    except:
        try:
            body = driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.ESCAPE)
            click_element(elem, sleep)
        except:
            print("Failed to click button")
        
