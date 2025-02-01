from typing import List, Optional, Callable
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement


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

def click_element(elem: WebElement, sleep: int = 1):
    elem.click()
    time.sleep(sleep)

def click_element_close_model(driver: webdriver.Chrome, elem: WebElement, sleep: int = 1):
    try:
        click_element(elem, sleep)
    except :
        body = driver.find_element(By.TAG_NAME, "body")
        body.send_keys(Keys.ESCAPE)
        click_element(elem, sleep)
