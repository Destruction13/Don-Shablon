"""Selenium automation for Yandex Calendar.

This script opens Yandex.Calendar with an existing user profile, finds all active
(red) events, checks the number of participants via a tooltip and opens events
with four or fewer participants in a new tab.
"""

from __future__ import annotations

import re
import time
from typing import Iterable

import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


# -------- Configuration --------

# Path to the browser user data directory (change to your real profile path)
USER_DATA_DIR = r"C:\\Users\\<USERNAME>\\AppData\\Local\\Yandex\\YandexBrowser\\User Data"

# Path to browser binary if needed (for Yandex Browser)
BROWSER_BINARY = r"C:\\Users\\<USERNAME>\\AppData\\Local\\Yandex\\YandexBrowser\\Application\\browser.exe"

# Target calendar URL
CALENDAR_URL = "https://calendar.yandex-team.ru/event?moreParams=1&uid=1120000000817192"

# Optional delay between actions to mimic human behaviour
ACTION_DELAY = 1.0


# -------- Helper functions --------

def create_driver() -> webdriver.Chrome:
    """Create Chrome driver with the specified profile."""
    options = Options()
    options.add_argument(f"--user-data-dir={USER_DATA_DIR}")
    options.binary_location = BROWSER_BINARY
    # Suppress automation flag
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    return driver


def is_red(slot: webdriver.remote.webelement.WebElement) -> bool:
    """Return True if slot color is roughly red.

    The heuristic checks ``background-color``. It logs the class attribute for
    future debugging because selectors may change.
    """
    color = slot.value_of_css_property("background-color")
    logging.debug("Slot class '%s' has color %s", slot.get_attribute("class"), color)

    match = re.search(r"rgba?\((\d+),\s*(\d+),\s*(\d+)", color)
    if not match:
        return False

    r, g, b = map(int, match.groups())
    # heuristic: r > 200, g < 100, b < 100 means the element is red-ish
    return r > 200 and g < 100 and b < 100


def find_red_slots(driver: webdriver.Chrome) -> list[webdriver.remote.webelement.WebElement]:
    """Return list of calendar slots that are highlighted in red."""
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
    )

    # TODO: choose more precise selector for calendar slots. "div" is generic
    # and may need refinement after inspecting the page markup.
    slots = driver.find_elements(By.CSS_SELECTOR, "div")
    red_slots = [slot for slot in slots if is_red(slot)]
    logging.info("Found %d red slots", len(red_slots))
    return red_slots


def parse_participants(
    driver: webdriver.Chrome,
    slot: webdriver.remote.webelement.WebElement,
) -> tuple[list[str], bool]:
    """Hover over slot, wait for tooltip and parse participants."""

    ActionChains(driver).move_to_element(slot).perform()

    # Selector may need adjustment according to actual tooltip markup
    tooltip_selector = ".popup__content"
    tooltip = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, tooltip_selector))
    )

    participant_blocks: Iterable[webdriver.remote.webelement.WebElement] = tooltip.find_elements(
        By.CSS_SELECTOR, "[data-testid='participant'], .participant"
    )
    participants = [p.text.strip() for p in participant_blocks if p.text.strip()]

    more_elems = tooltip.find_elements(By.XPATH, "//*[contains(text(), 'Ещё') or contains(text(), 'Еще')]")
    has_more = bool(more_elems)

    return participants, has_more


def open_event(driver: webdriver.Chrome, slot: webdriver.remote.webelement.WebElement) -> None:
    """Open the event linked with ``slot`` in a new tab."""

    slot.click()
    WebDriverWait(driver, 15).until(EC.url_contains("/event/"))
    href = driver.current_url
    logging.info("Opening event %s", href)
    driver.execute_script("window.open(arguments[0], '_blank');", href)
    driver.get(CALENDAR_URL)


# -------- Main logic --------

def main() -> None:
    driver = create_driver()
    try:
        driver.get(CALENDAR_URL)
        red_slots = find_red_slots(driver)

        for slot in red_slots:
            participants, has_more = parse_participants(driver, slot)
            logging.info("Participants %s, has_more=%s", participants, has_more)

            if has_more or len(participants) > 4:
                logging.info("Ignore event due to participant count")
                continue

            open_event(driver, slot)
            time.sleep(ACTION_DELAY)

        logging.info("Done")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
