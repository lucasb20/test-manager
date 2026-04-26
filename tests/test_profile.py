import pytest
from playwright.sync_api import Page, expect

@pytest.fixture(scope="function", autouse=True)
def before_each_after_each(page: Page, login_url, profile_url):
    page.goto(login_url)
    page.get_by_role("textbox", name="Email").fill("test@gmail.com")
    page.get_by_role("textbox", name="Password").fill("Test@123")
    page.goto(profile_url)
    yield
    page.goto(profile_url)
    page.get_by_role("link", name="Edit Profile").click()
    page.get_by_role("textbox", name="Name").fill("Test User")
    page.get_by_role("textbox", name="Email").fill("test@gmail.com")
    page.get_by_role("button", name="Save").click()

def test_edit_name(page: Page, profile_url):
    page.get_by_role("link", name="Edit Profile").click()
    page.get_by_role("textbox", name="Name").fill("New Name")
    page.get_by_role("button", name="Save").click()
    expect(page.locator("section")).to_contain_text("New Name")

def test_edit_email(page: Page, profile_url):
    page.get_by_role("link", name="Edit Profile").click()
    page.get_by_role("textbox", name="Email").fill("new_email@gmail.com")
    page.get_by_role("button", name="Save").click()
    expect(page.locator("section")).to_contain_text("new_email@gmail.com")

def test_change_password(page: Page, profile_url):
    page.get_by_role("link", name="Reset Password").click()
    page.get_by_role("textbox", name="New Password").fill("Test@123")
    page.get_by_role("textbox", name="Confirm Password").fill("Test@123")
    page.get_by_role("button", name="Reset Password").click()
    expect(page.get_by_role("alert")).to_contain_text("Password reset successfully.")
