import os
import shutil
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


def setup_driver(headless=True):
    """
    Set up the Selenium WebDriver with Chrome.

    :param headless: A boolean indicating whether to run Chrome in headless mode.
    :type headless: bool
    :return: A Selenium WebDriver instance configured with Chrome options.
    :rtype: selenium.webdriver.Chrome
    """
    options = Options()
    if headless:
        options.add_argument("--headless")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def record_version(source_url, version_info):
    """
    Record the version information and download date to a log file.

    :param source_url: The URL where the CORUM file was downloaded from.
    :type source_url: str
    :param version_info: The version information of the CORUM file.
    :type version_info: str
    """
    with open("version_log.txt", "w") as version_file:
        version_file.write(f"Version: {version_info}\n")
        version_file.write(f"Download Date: {time.strftime('%Y-%m-%d')}\n")
        version_file.write(f"Source URL: {source_url}\n")


def download_file():
    """
    Download the CORUM file from the specified URL.

    This function automates the process of downloading a file from the
    CORUM database using Selenium WebDriver. It navigates to the download
    page, interacts with the required elements to initiate the download,
    and moves the downloaded file to the current working directory.

    :raises Exception: If any error occurs during the file download or
                       movement process.
    """
    driver = setup_driver()
    try:
        source_url = "https://mips.helmholtz-muenchen.de/corum/download"
        driver.get(source_url)
        time.sleep(5)

        element = driver.find_element(
            By.XPATH,
            "//*[contains(concat( ' ', @class, ' ' ), concat( ' ', 'q-item__label', ' ' ))]",
        )
        version_info = element.text
        record_version(source_url, version_info)

        download_icon = driver.find_element(
            By.CSS_SELECTOR,
            ".q-card:nth-child(2) .q-item__section:nth-child(4) > .q-icon",
        )
        download_icon.click()
        time.sleep(5)

        download_button = driver.find_element(
            By.CSS_SELECTOR, ".q-card__section:nth-child(2) .q-btn__content"
        )
        download_button.click()
        time.sleep(10)

        download_path = os.path.expanduser("~/Downloads/corum_allComplexes.txt")
        destination_path = os.path.join(os.getcwd(), "allComplexes.txt")

        if os.path.exists(download_path):
            shutil.move(download_path, destination_path)
        else:
            raise FileNotFoundError(f"Downloaded file not found at {download_path}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()


# Execute the download function
download_file()
