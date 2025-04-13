import logging
from typing import Dict, List, Optional

from playwright.sync_api import Page

from vfs_appointment_bot.utils.date_utils import extract_date_from_string
from vfs_appointment_bot.vfs_bot.vfs_bot import VfsBot


class VfsBotNl(VfsBot):
    """
    VFS bot implementation for Netherlands visa applications via Dublin, Ireland.
    """

    def __init__(self, source_country_code: str):
        super().__init__()
        self.source_country_code = source_country_code
        self.destination_country_code = "NL"
        self.appointment_param_keys = [
            "visa_center",
            "visa_category",
            "visa_sub_category"
        ]

    def login(self, page: Page, email_id: str, password: str) -> None:
        """
        Performs login steps specific to the Netherlands VFS website.

        Args:
            page (playwright.sync_api.Page): The Playwright page object used for browser interaction.
            email_id (str): The user's email address for VFS login.
            password (str): The user's password for VFS login.

        Raises:
            Exception: If login fails due to unexpected errors or missing elements.
        """

        # Wait for login form elements
        try:
            page.wait_for_selector("#email", timeout=30000)
            logging.info("Email input found")
            page.wait_for_selector("#password", timeout=30000)
            logging.info("Password input found")
            
        except Exception as e:
            logging.error("Login form elements not found after waiting")
            raise Exception("Login form elements not found. The page might be stuck in a loading state.")

        
        # Add small delays between actions to appear more human-like
        page.wait_for_timeout(1000)
        
        # Fill in the login form
        email_input = page.locator("#email")
        password_input = page.locator("#password")

        email_input.fill(email_id)
        page.wait_for_timeout(500)
        password_input.fill(password)
        page.wait_for_timeout(1000)

        # Click the login button
        page.get_by_role("button", name="Sign In").click()
        
        # Wait for successful login by checking for the "Start New Booking" button
        try:
            page.wait_for_selector("role=button >> text=Start New Booking", timeout=30000)
        except Exception as e:
            logging.error("Failed to find 'Start New Booking' button after login")
            raise Exception("Login might have failed or the page is stuck in a loading state.")

    def pre_login_steps(self, page: Page) -> None:
        """
        Performs pre-login steps specific to the Netherlands VFS website.

        Args:
            page (playwright.sync_api.Page): The Playwright page object used for browser interaction.
        """
        # Handle cookie policies if they appear
        policies_reject_button = page.get_by_role("button", name="Accept Only Necessary")
        if policies_reject_button is not None:
            policies_reject_button.click()
            logging.debug("Rejected all cookie policies")

    def check_for_appontment(
        self, page: Page, appointment_params: Dict[str, str]
    ) -> Optional[List[str]]:
        """
        Checks for appointments on the Netherlands VFS website based on provided parameters.

        Args:
            page (playwright.sync_api.Page): The Playwright page object used for browser interaction.
            appointment_params (Dict[str, str]): A dictionary containing appointment search criteria.

        Returns:
            Optional[List[str]]: List of available appointment dates if found, None otherwise.
        """
        try:
            # Click Start New Booking button
            page.get_by_role("button", name="Start New Booking").click()
            
            # Select visa center
            page.get_by_label("Visa Application Centre").select_option(
                appointment_params["visa_center"]
            )
            
            # Select visa category
            page.get_by_label("Visa Category").select_option(
                appointment_params["visa_category"]
            )
            
            # Select visa subcategory
            page.get_by_label("Visa Sub Category").select_option(
                appointment_params["visa_sub_category"]
            )
            
            
            # Click continue and wait for available dates
            page.get_by_role("button", name="Continue").click()
            
            # Wait for and extract available dates
            dates_element = page.wait_for_selector(".date-available")
            if dates_element:
                dates_text = dates_element.inner_text()
                return extract_date_from_string(dates_text)
            
            return None
            
        except Exception as e:
            logging.error(f"Error checking for appointments: {str(e)}")
            return None 