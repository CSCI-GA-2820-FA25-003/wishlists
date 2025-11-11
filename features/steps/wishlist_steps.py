######################################################################
# Copyright 2016, 2024 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################
# pylint: disable=function-redefined, missing-function-docstring
# flake8: noqa

"""
Wishlist Steps

Steps file for Wishlist.feature

For information on Waiting until elements are present in the HTML see:
    https://selenium-python.readthedocs.io/waits.html
"""
import requests
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from behave import given, when, then  # pylint: disable=no-name-in-module


# HTTP Return Codes
HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_204_NO_CONTENT = 204

WAIT_TIMEOUT = 60


def _set_input_by_id(context, element_id, value):
    el = WebDriverWait(context.driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.ID, element_id))
    )
    el.clear()
    el.send_keys(value)


def _click_by_id(context, element_id):
    el = WebDriverWait(context.driver, WAIT_TIMEOUT).until(
        EC.element_to_be_clickable((By.ID, element_id))
    )
    el.click()


def _container_text(context, container_id):
    el = WebDriverWait(context.driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.ID, container_id))
    )
    return el.text


@given("the Flask wishlist service is running")
def step_impl(context):
    """Start a Chrome browser and open the app"""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    context.driver = webdriver.Chrome(options=options)
    context.base_url = "http://localhost:8080"


@given(
    'an item exists in wishlist with product_id "{product_id}" named "{name}" with price "{price}"'
)
def step_impl(context, product_id, name, price):
    """Create an item in the current wishlist via the API."""
    assert hasattr(context, "created_wishlist_id"), "No wishlist created yet."

    payload = {
        "product_id": int(product_id),
        "product_name": name,
        "price": float(price),
    }
    response = requests.post(
        f"{context.base_url}/wishlists/{context.created_wishlist_id}/items",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=WAIT_TIMEOUT,
    )
    assert (
        response.status_code == HTTP_201_CREATED
    ), f"Failed to create item: {response.status_code} {response.text}"

    # Save the created item and its ID to context
    context.created_item = response.json()
    context.created_item_id = context.created_item.get("id")
    assert context.created_item_id, "Item id was not returned by the service."


@when("I copy the created wishlist id into the wishlist field")
def step_impl(context):
    """Populate the wishlist ID field with the previously created wishlist."""
    assert (
        hasattr(context, "created_wishlist_id") and context.created_wishlist_id
    ), "No wishlist id is available in context."
    element = context.driver.find_element(By.ID, "wishlist_id")
    element.clear()
    element.send_keys(str(context.created_wishlist_id))


@when('I set the "Filter Wishlists" field to "{text}"')
def step_impl(context, text):
    """In Filter Wishlists Enter the keyword"""
    _set_input_by_id(context, "filter_wishlist_name", text)


@when('I press the "Search Wishlists" filter button')
def step_impl(context):
    """Click Filter session's Search Wishlists Button"""
    _click_by_id(context, "filter_wishlists-btn")


@then('I should see "{text}" in the wishlist results')
def step_impl(context, text):
    """Verify wishlist Result have Keyword"""
    body = _container_text(context, "search_results")
    assert text in body, f'"{text}" not found in wishlist results'


@then('I should see "Wishlist" in the page header above the wishlist results')
def step_impl(context):
    """Verify the heading still exist when click button"""
    header = (
        WebDriverWait(context.driver, WAIT_TIMEOUT)
        .until(EC.presence_of_element_located((By.CSS_SELECTOR, "#search_results h3")))
        .text
    )
    assert "Wishlist" in header, "Wishlist header not visible above results"
