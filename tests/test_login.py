import re
import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost"
LOGIN_URL = BASE_URL + "/auth/login"
REGISTER_URL = BASE_URL + "/auth/register"

def test_successful_login(page: Page):
    page.goto(LOGIN_URL)
    page.get_by_role("textbox", name="Email").fill("test@gmail.com")
    page.get_by_role("textbox", name="Password").fill("Test@123")
    expect(page.get_by_role("alert")).to_contain_text("Hello, Test User!")

def test_logout(page: Page):
    page.goto(LOGIN_URL)
    page.get_by_role("textbox", name="Email").fill("test@gmail.com")
    page.get_by_role("textbox", name="Password").fill("Test@123")
    page.get_by_role("link", name="Log Out").click()
    expect(page.get_by_role("paragraph")).to_contain_text("Please log in to manage your tests.")

def test_unsuccessful_login(page: Page):
    page.goto(LOGIN_URL)
    page.get_by_role("textbox", name="Email").fill("invalid@gmail.com")
    page.get_by_role("textbox", name="Password").fill("Test@123")
    expect(page.get_by_role("alert")).to_contain_text("Invalid email or password.")

def test_successfull_register(page: Page):
    page.goto(REGISTER_URL)
    page.get_by_role("textbox", name="Name").fill("New User")
    page.get_by_role("textbox", name="Email").fill("new_user@gmail.com")
    page.get_by_role("textbox", name="Password", exact=True).fill("Test@123")
    page.get_by_role("textbox", name="Confirm Password").fill("Test@123")
    page.get_by_role("button", name="Register").click()
    expect(page.get_by_role("alert")).to_contain_text("Registration successful!")

def test_unsuccessfull_register(page: Page):
    page.goto(REGISTER_URL)
    page.get_by_role("textbox", name="Name").fill("Invalid User")
    page.get_by_role("textbox", name="Email").fill("existing_user@gmail.com")
    page.get_by_role("textbox", name="Password", exact=True).fill("Test@123")
    page.get_by_role("textbox", name="Confirm Password").fill("Test@123")
    page.get_by_role("button", name="Register").click()
    expect(page.get_by_role("alert")).to_contain_text("Email already registered.")

def test_password_recovery(page: Page):
    assert 0 # Work in progress
    # TODO: GET /email?subject="Password Reset"
    email = emails[0]["text"]
    reset_link = re.search("http://.*", email).group(0)
    page.goto(reset_link)
    page.get_by_role("textbox", name="New Password").fill("Test@123")
    page.get_by_role("textbox", name="Confirm Password").fill("Test@123")
    page.get_by_role("button", name="Reset Password").click()
    expect(page.get_by_role("alert")).to_contain_text("Password has been reset.")
