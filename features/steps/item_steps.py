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
Item Steps

Steps file for Item.feature

For information on Waiting until elements are present in the HTML see:
    https://selenium-python.readthedocs.io/waits.html
"""
import requests
from behave import given, when, then  # pylint: disable=no-name-in-module
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# HTTP Return Codes
HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_204_NO_CONTENT = 204
HTTP_409_CONFLICT = 409

WAIT_TIMEOUT = 60


@given('no wishlist exists for customer "{customer_id}" named "{name}"')
def step_impl(context, customer_id, name):
    """Ensure there is no wishlist with the given customer/name combination."""
    response = requests.get(
        f"{context.base_url}/wishlists",
        params={"customer_id": customer_id, "name": name},
        timeout=WAIT_TIMEOUT,
    )
    assert response.status_code == HTTP_200_OK, (
        f"Failed to query wishlists for cleanup. Status: {response.status_code}, "
        f"Body: {response.text}"
    )
    for wishlist in response.json():
        requests.delete(
            f"{context.base_url}/wishlists/{wishlist['id']}",
            timeout=WAIT_TIMEOUT,
        )


@given('a wishlist exists for customer "{customer_id}" named "{name}"')
def step_impl(context, customer_id, name):
    """Create a wishlist via the API to support item scenarios."""
    payload = {
        "customer_id": customer_id,
        "name": name,
        "description": "Auto-generated for item feature",
    }
    response = requests.post(
        f"{context.base_url}/wishlists",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=WAIT_TIMEOUT,
    )
    if response.status_code == HTTP_201_CREATED:
        context.created_wishlist = response.json()
    elif response.status_code == HTTP_409_CONFLICT:
        search = requests.get(
            f"{context.base_url}/wishlists",
            params={"customer_id": customer_id, "name": name},
            timeout=WAIT_TIMEOUT,
        )
        assert search.status_code == HTTP_200_OK, (
            f"Failed to query wishlist during conflict resolution. "
            f"Status: {search.status_code}, Body: {search.text}"
        )
        found = search.json()
        assert found, "Expected at least one wishlist in search results."
        context.created_wishlist = found[0]
    else:
        raise AssertionError(
            f"Unexpected response creating wishlist: "
            f"{response.status_code} {response.text}"
        )
    context.created_wishlist_id = context.created_wishlist.get("id")
    assert context.created_wishlist_id, "Wishlist id was not returned by the service."

    # Ensure the wishlist has no lingering items to avoid conflicts during creation.
    requests.put(
        f"{context.base_url}/wishlists/{context.created_wishlist_id}/clear",
        timeout=WAIT_TIMEOUT,
    )


@when("I copy the created item id into the item id field")
def step_impl(context):
    """Populate the item ID field with the previously created item."""
    assert (
        hasattr(context, "created_item_id") and context.created_item_id
    ), "No item id is available in context. Create an item before using this step."
    element = context.driver.find_element(By.ID, "item_id")
    element.clear()
    element.send_keys(str(context.created_item_id))


@when(
    'an item exists in wishlist with product_id "{product_id}" named "{name}" with price "{price}"'
)
def step_impl(context, product_id, name, price):
    """Create an item in the current wishlist via API."""
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
    assert response.status_code in [
        HTTP_201_CREATED,
        HTTP_200_OK,
    ], f"Failed to create item: {response.status_code} {response.text}"
    context.created_item = response.json()
    context.created_item_id = context.created_item.get("id")
    assert context.created_item_id, "Item ID not returned by service."


@when('I click the "Delete Item" button')
def step_impl(context):
    """Click the Delete Item button."""
    WebDriverWait(context.driver, 10).until(
        EC.presence_of_element_located((By.ID, "delete_item-btn"))
    )
    btn = context.driver.find_element(By.ID, "delete_item-btn")
    btn.click()


@then('"{item_name}" should not appear in the item list')
def step_impl(context, item_name):
    """Verify the deleted item no longer appears in the item list."""
    WebDriverWait(context.driver, 10).until(
        EC.presence_of_element_located((By.ID, "search_results"))
    )
    table = context.driver.find_element(By.ID, "search_results")
    text = table.text
    assert item_name not in text, f'Item "{item_name}" was still found in the list.'


@when("I copy the created wishlist id into the item form")
def step_impl(context):
    """Wait for and fill in the wishlist id field on the item form."""
    assert hasattr(context, "created_wishlist_id"), "No wishlist id available."
    WebDriverWait(context.driver, 10).until(
        EC.presence_of_element_located((By.ID, "item_wishlist_id"))
    )
    element = context.driver.find_element(By.ID, "item_wishlist_id")
    element.clear()
    element.send_keys(str(context.created_wishlist_id))
