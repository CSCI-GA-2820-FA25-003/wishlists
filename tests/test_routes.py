# pylint: disable=too-many-lines
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

"""
Wishlist Service API Service Test Suite
"""
import os
import logging
from unittest import TestCase
from wsgi import app
from tests.factories import WishlistFactory, ItemFactory
from service.common import status
from service.models import db, Wishlist, Item

# from service.common.error_handlers import forbidden, internal_server_error


DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/postgres"
)
BASE_URL = "/api/wishlists"


######################################################################
#  T E S T   C A S E S
######################################################################
class TestWishlistService(TestCase):  # pylint: disable=too-many-public-methods
    """Wishlist Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        app.app_context().push()

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Wishlist).delete()  # clean up the last tests
        db.session.commit()

        self.api_key = app.config.get("API_KEY")

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    def _get_auth_headers(self, content_type="application/json", customer_id=None):
        """Helper to get headers with API key and optional customer ID"""
        headers = {
            "X-Api-Key": self.api_key,
        }
        if content_type:
            headers["Content-Type"] = content_type
        if customer_id:
            headers["X-Customer-Id"] = customer_id
        return headers

    ######################################################################
    #  P L A C E   T E S T   C A S E S   H E R E
    ######################################################################
    def test_health(self):
        """It should get the health endpoint"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_index_route_returns_index_html(self):
        """It should return the index.html UI page"""
        client = app.test_client()
        response = client.get("/")

        assert response.status_code == 200

        assert b"<html" in response.data

        content_type = response.headers.get("Content-Type")
        assert "text/html" in content_type

    def test_index(self):
        """It should call the home page api"""
        resp = self.client.get("/api-info")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["name"], "Wishlist Service")
        self.assertEqual(data["version"], "1.0.0")
        self.assertEqual(data["description"], "RESTful service for managing wishlists")
        # self.assertIn("wishlists", data["paths"])
        self.assertIn("paths", data)
        self.assertIsInstance(data["paths"], dict)
        paths = data["paths"]

        expected_keys = {
            "list_all_wishlists",
            "create_wishlist",
            "get_wishlist",
            "update_wishlist",
            "delete_wishlist",
            "list_wishlist_items",
            "create_wishlist_item",
            "get_wishlist_item",
            "update_wishlist_item",
            "delete_wishlist_item",
            "clear_wishlist",
            "share_wishlist",
        }
        self.assertTrue(expected_keys.issubset(paths.keys()))
        self.assertTrue(paths["list_all_wishlists"].endswith("/wishlists"))
        self.assertTrue(paths["create_wishlist"].endswith("/wishlists"))
        self.assertIn("/wishlists/{wishlist_id}", paths["get_wishlist"])
        self.assertIn("/wishlists/{wishlist_id}", paths["update_wishlist"])
        self.assertIn("/wishlists/{wishlist_id}", paths["delete_wishlist"])

        self.assertIn("/wishlists/{wishlist_id}/items", paths["list_wishlist_items"])
        self.assertIn("/wishlists/{wishlist_id}/items", paths["create_wishlist_item"])

        self.assertIn(
            "/wishlists/{wishlist_id}/items/{item_id}", paths["get_wishlist_item"]
        )
        self.assertIn(
            "/wishlists/{wishlist_id}/items/{item_id}", paths["update_wishlist_item"]
        )
        self.assertIn(
            "/wishlists/{wishlist_id}/items/{item_id}", paths["delete_wishlist_item"]
        )
        # Verify action endpoints
        self.assertIn("/wishlists/{wishlist_id}/clear", paths["clear_wishlist"])
        self.assertIn("/wishlists/{wishlist_id}/share", paths["share_wishlist"])

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_wishlists(self, count, customer_id=None):
        """
        Factory method to create wishlists in bulk directly in the database
        """
        wishlists = []
        for _ in range(count):
            if customer_id:
                wishlist = WishlistFactory(customer_id=customer_id)
            else:
                wishlist = WishlistFactory()

            wishlist.create()  #
            wishlists.append(wishlist)
        return wishlists

    ######################################################################
    #  W I S H L I S T   T E S T   C A S E S
    ######################################################################

    def test_get_wishlist_list(self):
        """It should Get a list of Wishlists"""
        self._create_wishlists(5)
        resp = self.client.get(BASE_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 5)

    def test_create_wishlist(self):
        """It should Create a new Wishlist"""
        wishlist = WishlistFactory()
        resp = self.client.post(
            BASE_URL,
            json=wishlist.serialize(),
            content_type="application/json",
            headers=self._get_auth_headers(),
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = resp.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_wishlist = resp.get_json()
        self.assertEqual(
            new_wishlist["customer_id"],
            wishlist.customer_id,
            "Customer IDs do not match",
        )
        self.assertEqual(new_wishlist["name"], wishlist.name, "Names do not match")
        self.assertEqual(
            new_wishlist["description"],
            wishlist.description,
            "Descriptions do not match",
        )
        # self.assertEqual(new_wishlist["items"], wishlist.items, "Items do not match")

    def test_create_wishlist_no_content_type(self):
        """It should return 415 when Content-Type header is missing"""
        wishlist = WishlistFactory()

        resp = self.client.post(
            BASE_URL,
            data=str(wishlist.serialize()),
            headers={"X-Api-Key": self.api_key},
        )

        self.assertEqual(resp.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
        data = resp.get_json()
        self.assertIn("Content-Type", data["message"])

    def test_create_wishlist_bad_payload(self):
        """It should fail with 400 BAD_REQUEST when request body is missing required fields"""
        resp = self.client.post(
            BASE_URL,
            json={"description": "only desc"},
            content_type="application/json",
            headers=self._get_auth_headers(),
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.get_json()
        self.assertEqual(data["status"], status.HTTP_400_BAD_REQUEST)
        self.assertIn("Bad Request", data["error"])

    def test_create_wishlist_method_not_allowed(self):
        """It should return 405 METHOD_NOT_ALLOWED when using an unsupported HTTP method"""
        resp = self.client.put(BASE_URL, json={}, headers=self._get_auth_headers())
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        # data = resp.get_json()
        # self.assertEqual(data["status"], status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_create_wishlist_wrong_content_type(self):
        """It should fail with 415 UNSUPPORTED_MEDIA_TYPE when Content-Type is not application/json"""
        resp = self.client.post(
            BASE_URL,
            data="{}",
            headers=self._get_auth_headers(content_type="text/html"),
        )
        self.assertEqual(resp.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
        # data = resp.get_json()
        # self.assertEqual(data["status"], status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_delete_wishlist_success(self):
        """It should delete a Wishlist and return 204 NO_CONTENT"""
        # Create a wishlist first
        wishlist = WishlistFactory()
        resp = self.client.post(
            BASE_URL, json=wishlist.serialize(), headers=self._get_auth_headers()
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        wishlist_id = resp.get_json()["id"]

        # Sanity: it exists in DB
        self.assertIsNotNone(Wishlist.find(wishlist_id))

        # Delete it
        resp = self.client.delete(
            f"{BASE_URL}/{wishlist_id}", headers={"X-Api-Key": self.api_key}
        )
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        # No response body for 204
        self.assertEqual(resp.data, b"")

        # Verify removed from DB
        self.assertIsNone(Wishlist.find(wishlist_id))

    # def test_delete_wishlist_not_found(self):
    #     """It should return 404 NOT_FOUND when deleting a non-existent Wishlist"""
    #     resp = self.client.delete(f"{BASE_URL}/0")
    #     self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
    #     data = resp.get_json()
    #     self.assertEqual(data["status"], status.HTTP_404_NOT_FOUND)
    #     self.assertIn("Not Found", data["error"])

    def test_get_wishlist(self):
        """It should Get a single Wishlist"""
        # get the id of a wishlist
        test_wishlist = self._create_wishlists(1)[0]
        response = self.client.get(f"{BASE_URL}/{test_wishlist.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["name"], test_wishlist.name)
        self.assertEqual(data["customer_id"], test_wishlist.customer_id)
        self.assertEqual(data["description"], test_wishlist.description)

    def test_get_wishlist_not_found(self):
        """It should not Get a Wishlist that's not found"""
        response = self.client.get(f"{BASE_URL}/0")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.get_json()
        logging.debug("Response data = %s", data)
        self.assertIn("was not found", data["message"])

    def test_update_wishlist_success(self):
        """It should successfully update an existing wishlist's name and return 200 OK."""
        created = self._create_wishlists(1)[0]
        wishlist_id = created.id
        owner_id = created.customer_id

        # Update Name
        resp = self.client.put(
            f"{BASE_URL}/{wishlist_id}",
            json={"name": "Holiday Gifts"},
            headers=self._get_auth_headers(customer_id=owner_id),
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        body = resp.get_json()
        self.assertEqual(body["id"], wishlist_id)
        self.assertEqual(body["customer_id"], owner_id)
        self.assertEqual(body["name"], "Holiday Gifts")

    def test_update_wishlist_not_found(self):
        """It should return 404 Not Found when wishlist does not exist"""
        resp = self.client.put(
            f"{BASE_URL}/0",
            json={"name": "Holiday Gifts"},
            headers=self._get_auth_headers(customer_id="User0001"),
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        body = resp.get_json()
        self.assertIn("not found", body.get("message", "").lower())

    def test_update_wishlist_forbidden(self):
        """It should return 403 Forbidden when a non-owner tries to update"""
        created = self._create_wishlists(1)[0]
        wishlist_id = created.id

        resp = self.client.put(
            f"{BASE_URL}/{wishlist_id}",
            json={"name": "Nope"},
            headers=self._get_auth_headers(customer_id="IntruderB"),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_wishlist_missing_api_key(self):
        """It should return 401 when API key is missing"""
        wishlist = WishlistFactory()
        resp = self.client.post(
            BASE_URL,
            json=wishlist.serialize(),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_wishlist_invalid_api_key(self):
        """It should return 401 when API key is invalid"""
        wishlist = WishlistFactory()
        resp = self.client.post(
            BASE_URL,
            json=wishlist.serialize(),
            headers={"Content-Type": "application/json", "X-Api-Key": "wrong-key"},
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_wishlist_description(self):
        """It should update wishlist description"""
        created = self._create_wishlists(1)[0]
        wishlist_id = created.id
        owner_id = created.customer_id

        # Update description
        resp = self.client.put(
            f"{BASE_URL}/{wishlist_id}",
            json={"description": "New description here"},
            headers=self._get_auth_headers(customer_id=owner_id),
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        body = resp.get_json()
        self.assertEqual(body["description"], "New description here")

    def test_update_wishlist_name_and_description(self):
        """It should update both name and description"""
        created = self._create_wishlists(1)[0]
        wishlist_id = created.id
        owner_id = created.customer_id

        # Update both
        resp = self.client.put(
            f"{BASE_URL}/{wishlist_id}",
            json={"name": "Updated Name", "description": "Updated Description"},
            headers=self._get_auth_headers(customer_id=owner_id),
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        body = resp.get_json()
        self.assertEqual(body["name"], "Updated Name")
        self.assertEqual(body["description"], "Updated Description")

    def test_update_wishlist_missing_api_key(self):
        """It should return 401 when updating without API key"""
        wishlist = self._create_wishlists(1)[0]
        resp = self.client.put(
            f"{BASE_URL}/{wishlist.id}",
            json={"name": "New Name"},
            headers={
                "Content-Type": "application/json",
                "X-Customer-Id": wishlist.customer_id,
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_wishlist_missing_api_key(self):
        """It should return 401 when deleting without API key"""
        wishlist = self._create_wishlists(1)[0]
        resp = self.client.delete(f"{BASE_URL}/{wishlist.id}")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    ######################################################################
    #  S H A R E   L I N K   T E S T S
    ######################################################################

    def test_share_wishlist_success(self):
        """It should generate a share URL for an existing wishlist and return 200"""
        wishlist = self._create_wishlists(1, customer_id="CUST001")[0]

        resp = self.client.put(f"{BASE_URL}/{wishlist.id}/share")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        body = resp.get_json()
        self.assertIn("share_url", body)
        # Should be an absolute URL that ends with /wishlists/{id}
        self.assertTrue(body["share_url"].endswith(f"{BASE_URL}/{wishlist.id}"))

    def test_share_wishlist_not_found(self):
        """It should return 404 when generating a link for a non-existent wishlist"""
        resp = self.client.put(f"{BASE_URL}/999/share")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    ######################################################################
    #  I T E M   T E S T   C A S E S
    ######################################################################
    def test_list_items_on_empty_wishlist(self):
        """It should Get an empty list of Items for an empty Wishlist"""
        wishlist = self._create_wishlists(1)[0]
        resp = self.client.get(f"{BASE_URL}/{wishlist.id}/items")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 0)

    #     # def test_get_wishlist_item(self):
    #     #     """It should Get a single Item from a Wishlist"""
    #     #     # Create a wishlist with an item
    #     #     wishlist = WishlistFactory()
    #     #     item = ItemFactory(wishlist=wishlist)
    #     #     wishlist.items.append(item)
    #     #     wishlist.create()

    #     # Retrieve the item
    #     response = self.client.get(f"{BASE_URL}/{wishlist.id}/items/{item.id}")
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)

    #     data = response.get_json()
    #     self.assertEqual(data["id"], item.id)
    #     self.assertEqual(data["product_id"], item.product_id)
    #     self.assertEqual(data["product_name"], item.product_name)
    #     self.assertEqual(data["wishlist_id"], wishlist.id)

    # def test_get_wishlist_item_not_found(self):
    #     """It should not Get an Item that doesn't exist"""
    #     # Create a wishlist without items
    #     wishlist = self._create_wishlists(1)[0]

    #     # Try to get non-existent item
    #     response = self.client.get(f"{BASE_URL}/{wishlist.id}/items/0")
    #     self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    #     data = response.get_json()
    #     self.assertIn("was not found", data["message"])

    # def test_get_item_wishlist_not_found(self):
    #     """It should not Get an Item if Wishlist doesn't exist"""
    #     response = self.client.get(f"{BASE_URL}/0/items/1")
    #     self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    #     data = response.get_json()
    #     self.assertIn("Wishlist", data["message"])

    def test_add_item_to_wishlist_success(self):
        """It should add a new item to a wishlist and return 201 with details"""
        # Arrange: create a wishlist
        wishlist = self._create_wishlists(1)[0]
        headers = {
            "Content-Type": "application/json",
            "X-User-Id": wishlist.customer_id,
        }
        payload = {
            "product_id": 123456,
            "product_name": "widget-pro",
            "prices": 19.99,
            "description": "fancy widget",
        }

        # Act
        resp = self.client.post(
            f"{BASE_URL}/{wishlist.id}/items", json=payload, headers=headers
        )

        # Assert
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("Location", resp.headers)
        data = resp.get_json()
        self.assertIsNotNone(data["id"])  # item id assigned
        self.assertEqual(data["wishlist_id"], wishlist.id)
        self.assertEqual(data["product_id"], payload["product_id"])
        self.assertEqual(data["product_name"], payload["product_name"])
        self.assertIn("wish_date", data)  # date snapshot
        self.assertIn("prices", data)
        self.assertAlmostEqual(data["prices"], payload["prices"], places=2)

        # Follow Location to ensure persistence
        item_url = resp.headers["Location"]
        get_resp = self.client.get(item_url)
        self.assertEqual(get_resp.status_code, status.HTTP_200_OK)
        fetched = get_resp.get_json()
        self.assertEqual(fetched["id"], data["id"])
        self.assertEqual(fetched["product_id"], payload["product_id"])

    def test_add_duplicate_item_conflict(self):
        """It should prevent duplicate items and return 409 Conflict"""
        wishlist = self._create_wishlists(1)[0]
        headers = {
            "Content-Type": "application/json",
            "X-User-Id": wishlist.customer_id,
        }
        payload = {"product_id": 98765, "product_name": "gadget", "prices": 9.99}

        # First add succeeds
        resp1 = self.client.post(
            f"{BASE_URL}/{wishlist.id}/items", json=payload, headers=headers
        )
        self.assertEqual(resp1.status_code, status.HTTP_201_CREATED)

        # Second add with same product_id should 409
        resp2 = self.client.post(
            f"{BASE_URL}/{wishlist.id}/items", json=payload, headers=headers
        )
        self.assertEqual(resp2.status_code, status.HTTP_409_CONFLICT)
        data = resp2.get_json()
        self.assertIn("already exists", data["message"])  # helpful message

    def test_add_item_invalid_product_id(self):
        """It should return 400 when product_id is invalid (non-existent/invalid)"""
        wishlist = self._create_wishlists(1)[0]
        headers = {
            "Content-Type": "application/json",
            "X-User-Id": wishlist.customer_id,
        }
        # Use an invalid product_id (0 or negative interpreted as invalid for this service)
        payload = {"product_id": 0, "product_name": "bad", "price": 5.55}
        resp = self.client.post(
            f"{BASE_URL}/{wishlist.id}/items", json=payload, headers=headers
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.get_json()
        self.assertIn("invalid product_id", data["message"].lower())

        # Also test non-integer product_id
        payload = {"product_id": "abc", "product_name": "bad", "price": 5.55}
        resp = self.client.post(
            f"{BASE_URL}/{wishlist.id}/items", json=payload, headers=headers
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.get_json()
        self.assertIn("product_id must be an integer", data["message"].lower())

    def test_add_item_to_nonexistent_wishlist(self):
        """It should return 404 when wishlist does not exist"""
        headers = {"Content-Type": "application/json", "X-User-Id": "User0001"}
        payload = {"product_id": 111, "product_name": "ghost", "price": 1.11}
        resp = self.client.post(f"{BASE_URL}/0/items", json=payload, headers=headers)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        data = resp.get_json()
        self.assertIn("Wishlist", data["message"])  # error mentions wishlist not found

    def test_add_item_missing_required_fields(self):
        """It should return 400 and mention missing fields when payload incomplete"""
        wishlist = self._create_wishlists(1)[0]
        headers = {
            "Content-Type": "application/json",
            "X-User-Id": wishlist.customer_id,
        }
        # Missing product_name
        payload = {"product_id": 222, "price": 2.22}
        resp = self.client.post(
            f"{BASE_URL}/{wishlist.id}/items", json=payload, headers=headers
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.get_json()
        self.assertIn("product_name", data["message"])  # indicates missing field

        # Missing price
        payload = {"product_id": 333, "product_name": "name-only"}
        resp = self.client.post(
            f"{BASE_URL}/{wishlist.id}/items", json=payload, headers=headers
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.get_json()
        self.assertIn("price", data["message"])  # indicates missing field

    def test_delete_wishlist_item_success(self):
        """It should delete an Item from a Wishlist and return 204 NO_CONTENT"""

        wishlist = WishlistFactory()
        item = ItemFactory(wishlist=wishlist)
        wishlist.items.append(item)
        wishlist.create()

        self.assertIsNotNone(item.id)

        resp = self.client.delete(f"{BASE_URL}/{wishlist.id}/items/{item.id}")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(resp.data, b"")

        self.assertIsNone(Item.find(item.id))

    def test_delete_wishlist_item_not_found(self):
        """It should return 204 when deleting a non-existent Item (idempotent)"""
        wishlist = self._create_wishlists(1)[0]

        resp = self.client.delete(f"{BASE_URL}/{wishlist.id}/items/0")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(resp.data, b"")

    def test_delete_wishlist_item_wrong_wishlist(self):
        """It should return 204 and NOT delete when item belongs to a different wishlist"""
        w1 = WishlistFactory()
        item = ItemFactory(wishlist=w1)
        w1.items.append(item)
        w1.create()

        w2 = WishlistFactory()
        w2.create()

        resp = self.client.delete(f"{BASE_URL}/{w2.id}/items/{item.id}")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

        self.assertIsNotNone(Item.find(item.id))

    def test_update_wishlist_item(self):
        """It should Update an existing Item in a Wishlist"""
        # Create a wishlist with an item
        wishlist = WishlistFactory()
        item = ItemFactory(wishlist=wishlist)
        wishlist.items.append(item)
        wishlist.create()

        # Update the item
        original_product_id = item.product_id
        updated_data = item.serialize()
        updated_data["product_id"] = 99999
        updated_data["product_name"] = "Updated Product Name"

        response = self.client.put(
            f"{BASE_URL}/{wishlist.id}/items/{item.id}",
            json=updated_data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify the update
        data = response.get_json()
        self.assertEqual(data["id"], item.id)
        self.assertEqual(data["product_id"], 99999)
        self.assertEqual(data["product_name"], "Updated Product Name")
        self.assertNotEqual(data["product_id"], original_product_id)

    def test_update_wishlist_item_not_found(self):
        """It should not Update an Item that doesn't exist"""
        # Create a wishlist without items
        wishlist = self._create_wishlists(1)[0]

        # Try to update non-existent item
        updated_data = {
            "wishlist_id": wishlist.id,
            "customer_id": "User0001",
            "product_id": 12345,
            "product_name": "Test Product",
            "prices": 29.99,
        }

        response = self.client.put(
            f"{BASE_URL}/{wishlist.id}/items/0",
            json=updated_data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.get_json()
        self.assertIn("was not found", data["message"])

    def test_update_item_wishlist_not_found(self):
        """It should not Update an Item if Wishlist doesn't exist"""
        updated_data = {
            "wishlist_id": 0,
            "customer_id": "User0001",
            "product_id": 12345,
            "product_name": "Test Product",
            "prices": 29.99,
        }

        response = self.client.put(
            f"{BASE_URL}/0/items/1", json=updated_data, content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.get_json()
        self.assertIn("Wishlist", data["message"])

    def test_update_item_wrong_wishlist(self):
        """It should not Update an Item that belongs to a different Wishlist"""
        # Create two wishlists with items
        wishlist1 = WishlistFactory()
        item1 = ItemFactory(wishlist=wishlist1)
        wishlist1.items.append(item1)
        wishlist1.create()

        wishlist2 = WishlistFactory()
        wishlist2.create()

        # Try to update item1 using wishlist2's ID
        updated_data = item1.serialize()
        updated_data["product_id"] = 99999

        response = self.client.put(
            f"{BASE_URL}/{wishlist2.id}/items/{item1.id}",
            json=updated_data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.get_json()
        self.assertIn("was not found in Wishlist", data["message"])

    def test_clear_wishlist_with_items(self):
        """Scenario: Clear all items from an existing wishlist -> 204 and items become empty"""
        # Given: a wishlist with 3 items
        wishlist = self._create_wishlists(1)[0]
        wid = wishlist.id

        # Create three distinct items via API to exercise full stack
        for i in range(3):
            payload = {
                "product_id": 1000 + i,  # ensure uniqueness per uq constraint
                "product_name": f"p-{i}",
                "prices": 9.99 + i,
            }
            resp = self.client.post(
                f"{BASE_URL}/{wid}/items",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-User-Id": wishlist.customer_id,
                },
            )
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # When: clear
        resp = self.client.put(f"{BASE_URL}/{wid}/clear")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

        # Then: items list is empty
        resp = self.client.get(f"{BASE_URL}/{wid}/items")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.get_json(), [])

        # And: wishlist itself still exists
        resp = self.client.get(f"{BASE_URL}/{wid}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_clear_already_empty_wishlist(self):
        """Scenario: Clear an already empty wishlist -> 204, no error"""
        wishlist = self._create_wishlists(1)[0]
        wid = wishlist.id

        # Sanity: empty
        resp = self.client.get(f"{BASE_URL}/{wid}/items")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.get_json(), [])

        # When: clear
        resp = self.client.put(f"{BASE_URL}/{wid}/clear")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

        # Idempotency: clearing again is still 204
        resp = self.client.put(f"{BASE_URL}/{wid}/clear")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_clear_nonexistent_wishlist(self):
        """Scenario: Attempt to clear a non-existent wishlist -> 404 with message"""
        resp = self.client.put(f"{BASE_URL}/999/clear")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        data = resp.get_json()
        self.assertIn("was not found", data["message"].lower())

    def test_query_with_invalid_parameter(self):
        """It should return 400 Bad Request for an invalid query parameter"""
        resp = self.client.get(BASE_URL, query_string="invalid_param=bad_value")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_query_wishlist_by_customer_id(self):
        """It should Query wishlists by customer_id"""

        self._create_wishlists(count=2, customer_id="CUST001")
        self._create_wishlists(count=1, customer_id="CUST999")

        resp = self.client.get(BASE_URL, query_string="customer_id=CUST001")  #

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["customer_id"], "CUST001")

    def test_query_wishlist_items_by_product_id(self):
        """It should return only the item matching the exact product_id filter"""
        # Given: a wishlist with 3 items (1001, 1002, 1003)
        wishlist = WishlistFactory()

        i1 = ItemFactory(wishlist=wishlist, product_id=1001)
        i2 = ItemFactory(wishlist=wishlist, product_id=1002)
        i3 = ItemFactory(wishlist=wishlist, product_id=1003)
        wishlist.items.extend([i1, i2, i3])
        wishlist.create()

        # When: querying by product_id=1002
        resp = self.client.get(
            f"{BASE_URL}/{wishlist.id}/items", query_string="product_id=1002"
        )

        # Then: only the item with product_id=1002 is returned
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["product_id"], 1002)
        # Sanity: ensure not returning others
        self.assertNotEqual(data[0]["product_id"], 1001)
        self.assertNotEqual(data[0]["product_id"], 1003)

    def test_query_wishlist_items_invalid_product_id(self):
        """It should return 400 Bad Request when product_id is non-numeric"""
        wishlist = self._create_wishlists(1)[0]
        resp = self.client.get(
            f"{BASE_URL}/{wishlist.id}/items", query_string="product_id=abc"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        body = resp.get_json()
        self.assertIn("product_id must be an integer", body.get("message", "").lower())

    def test_query_wishlist_by_customer_and_name_substring(self):
        """It should Query Wishlists by customer_id and name with substring match (case-insensitive)"""
        # This test matches the acceptance criteria exactly:
        # Given customer "CUST001" owns wishlists named "Holiday Gifts" and "Birthday Wishlist"
        customer1 = "CUST001"
        wishlist1 = WishlistFactory(customer_id=customer1, name="Holiday Gifts")
        wishlist2 = WishlistFactory(customer_id=customer1, name="Birthday Wishlist")

        # And another customer "CUST999" owns a wishlist named "Holiday Gifts"
        customer2 = "CUST999"
        wishlist3 = WishlistFactory(customer_id=customer2, name="Holiday Gifts")

        # Create all wishlists
        for wl in [wishlist1, wishlist2, wishlist3]:
            resp = self.client.post(
                BASE_URL, json=wl.serialize(), headers=self._get_auth_headers()
            )
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # When I send a GET request to /wishlists?customer_id=CUST001&name=gift
        resp = self.client.get(
            BASE_URL, query_string={"customer_id": customer1, "name": "gift"}
        )

        # Then I receive a 200 OK response
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.get_json()

        # And only "Holiday Gifts" belonging to "CUST001" is returned
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["customer_id"], customer1)
        self.assertEqual(data[0]["name"], "Holiday Gifts")

        # And no wishlist from other customers is included
        for wishlist in data:
            self.assertNotEqual(wishlist["customer_id"], customer2)

    def test_query_wishlist_by_name_without_customer_id(self):
        """It should return 400 BAD REQUEST when name is provided without customer_id"""
        # Create some wishlists
        self._create_wishlists(count=2)

        # Try to query by name only (without customer_id) - should fail
        resp = self.client.get(BASE_URL, query_string={"name": "Holiday"})

        # Should return 400 BAD REQUEST
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        # Verify the error message mentions customer_id is required
        data = resp.get_json()
        self.assertIn("customer_id is required", data["message"].lower())

    def test_query_items_by_partial_product_name(self):
        """It should filter items by partial product_name (case-insensitive substring)"""
        wl = WishlistFactory()
        i1 = ItemFactory(wishlist=wl, product_name="Blue Mug", product_id=10101)
        i2 = ItemFactory(wishlist=wl, product_name="Red Plate", product_id=20202)
        wl.items.extend([i1, i2])
        wl.create()

        resp = self.client.get(
            f"{BASE_URL}/{wl.id}/items", query_string={"product_name": "mug"}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["product_name"], "Blue Mug")

    def test_query_items_product_name_case_insensitive(self):
        """It should match product_name ignoring case"""
        wl = WishlistFactory()
        i1 = ItemFactory(wishlist=wl, product_name="Wireless Mouse", product_id=30303)
        wl.items.append(i1)
        wl.create()

        resp = self.client.get(
            f"{BASE_URL}/{wl.id}/items", query_string={"product_name": "MOUSE"}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        names = [x["product_name"] for x in resp.get_json()]
        self.assertIn("Wireless Mouse", names)

    def test_query_items_invalid_param_400(self):
        """It should return 400 Bad Request for unsupported item query params"""
        wl = WishlistFactory()
        wl.create()
        resp = self.client.get(
            f"{BASE_URL}/{wl.id}/items", query_string={"unknown_param": "abc"}
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        msg = resp.get_json().get("message", "").lower()
        self.assertIn("unsupported", msg)
        self.assertIn("unknown_param", msg)

    ######################################################################
    #  E R R O R   H A N D L E R   T E S T S
    ######################################################################

    # def test_error_handler_forbidden(self):
    #     """It should return a JSON 403 response from the forbidden error handler"""

    #     resp, code = forbidden(Exception("forbidden test"))
    #     self.assertEqual(code, status.HTTP_403_FORBIDDEN)
    #     data = resp.get_json()
    #     self.assertEqual(data["status"], status.HTTP_403_FORBIDDEN)
    #     self.assertEqual(data["error"], "Forbidden")
    #     self.assertIn("forbidden test", data["message"])

    # def test_error_handler_internal_server_error(self):
    #     """It should return a JSON 500 response from the internal server error handler"""

    #     resp, code = internal_server_error(Exception("boom"))
    #     self.assertEqual(code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    #     data = resp.get_json()
    #     self.assertEqual(data["status"], status.HTTP_500_INTERNAL_SERVER_ERROR)
    #     self.assertEqual(data["error"], "Internal Server Error")
    #     self.assertIn("boom", data["message"])

    def test_add_item_with_invalid_price(self):
        """It should return 400 when adding an item with invalid price"""
        wishlist = self._create_wishlists(1)[0]
        payload = {"product_id": 1, "product_name": "Test", "price": "not-a-number"}

        resp = self.client.post(
            f"{BASE_URL}/{wishlist.id}/items",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    ######################################################################
    #  S W A G G E R   D O C U M E N T A T I O N   T E S T S
    ######################################################################

    def test_swagger_ui_accessible(self):
        """It should access the Swagger UI"""
        # Test that Swagger documentation is accessible
        # The UI might be at different URLs depending on Flask-RESTX configuration,
        # so we verify the swagger.json spec is accessible
        resp = self.client.get("/api/swagger.json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        swagger_spec = resp.get_json()
        self.assertIn("swagger", swagger_spec)
        self.assertIn("info", swagger_spec)
        self.assertIn("paths", swagger_spec)

    def test_swagger_spec_contains_item_model(self):
        """It should include WishlistItem model in Swagger spec"""
        resp = self.client.get("/api/swagger.json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        swagger_spec = resp.get_json()

        # Check that the models are defined
        self.assertIn("definitions", swagger_spec)
        definitions = swagger_spec["definitions"]

        # Check for WishlistItem model
        self.assertIn("WishlistItem", definitions)
        item_model = definitions["WishlistItem"]

        # Verify required fields
        self.assertIn("required", item_model)
        required_fields = item_model["required"]
        self.assertIn("product_id", required_fields)
        self.assertIn("product_name", required_fields)
        self.assertIn("prices", required_fields)

        # Verify properties
        self.assertIn("properties", item_model)
        properties = item_model["properties"]
        self.assertIn("product_id", properties)
        self.assertIn("product_name", properties)
        self.assertIn("prices", properties)

        # Check field types
        self.assertEqual(properties["product_id"]["type"], "integer")
        self.assertEqual(properties["product_name"]["type"], "string")
        self.assertEqual(properties["prices"]["type"], "number")

        # Check descriptions exist
        self.assertIn("description", properties["product_id"])
        self.assertIn("description", properties["product_name"])
        self.assertIn("description", properties["prices"])

    def test_swagger_spec_contains_item_model_with_readonly_fields(self):
        """It should include WishlistItemModel with read-only fields"""
        resp = self.client.get("/api/swagger.json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        swagger_spec = resp.get_json()
        definitions = swagger_spec["definitions"]

        # Check for WishlistItemModel (the full model with read-only fields)
        self.assertIn("WishlistItemModel", definitions)
        item_model = definitions["WishlistItemModel"]

        # Flask-RESTX uses 'allOf' for inherited models
        # The model combines the parent with additional properties
        if "allOf" in item_model:
            # Get properties from the parent reference and additional properties
            all_properties = {}
            for schema in item_model["allOf"]:
                if "properties" in schema:
                    all_properties.update(schema["properties"])
                elif "$ref" in schema:
                    # Get properties from the referenced model
                    ref_name = schema["$ref"].split("/")[-1]
                    if (
                        ref_name in definitions
                        and "properties" in definitions[ref_name]
                    ):
                        all_properties.update(definitions[ref_name]["properties"])
            properties = all_properties
        else:
            properties = item_model.get("properties", {})

        # Verify that the additional read-only fields exist
        # (These are the fields added via api.inherit that aren't in the base WishlistItem model)
        self.assertIn("id", properties, "id field should exist in WishlistItemModel")
        self.assertIn("wishlist_id", properties, "wishlist_id field should exist")
        self.assertIn("customer_id", properties, "customer_id field should exist")
        self.assertIn("wish_date", properties, "wish_date field should exist")

        # Verify the id field is an integer
        self.assertEqual(properties["id"].get("type"), "integer")

    def test_swagger_post_items_endpoint_uses_model(self):
        """It should document POST /wishlists/{id}/items with WishlistItem model"""
        resp = self.client.get("/api/swagger.json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        swagger_spec = resp.get_json()

        # Navigate to the POST endpoint
        paths = swagger_spec.get("paths", {})
        items_path = "/wishlists/{wishlist_id}/items"

        self.assertIn(items_path, paths)
        self.assertIn("post", paths[items_path])

        post_spec = paths[items_path]["post"]

        # Check that it has parameters (request body)
        self.assertIn("parameters", post_spec)

        # Find the body parameter
        body_param = None
        for param in post_spec["parameters"]:
            if param.get("in") == "body":
                body_param = param
                break

        self.assertIsNotNone(body_param, "POST endpoint should have a body parameter")

        # Verify it references the WishlistItem model
        self.assertIn("schema", body_param)
        schema = body_param["schema"]
        self.assertIn("$ref", schema)
        self.assertIn("WishlistItem", schema["$ref"])

    def test_swagger_get_items_endpoint_returns_model(self):
        """It should document GET /wishlists/{id}/items returns array of WishlistItemModel"""
        resp = self.client.get("/api/swagger.json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        swagger_spec = resp.get_json()

        paths = swagger_spec.get("paths", {})
        items_path = "/wishlists/{wishlist_id}/items"

        self.assertIn(items_path, paths)
        self.assertIn("get", paths[items_path])

        get_spec = paths[items_path]["get"]

        # Check response schema
        self.assertIn("responses", get_spec)
        self.assertIn("200", get_spec["responses"])

        response_200 = get_spec["responses"]["200"]
        self.assertIn("schema", response_200)

        schema = response_200["schema"]
        # Should be an array of WishlistItemModel
        self.assertEqual(schema.get("type"), "array")
        self.assertIn("items", schema)
        self.assertIn("$ref", schema["items"])
        self.assertIn("WishlistItemModel", schema["items"]["$ref"])

    def test_swagger_item_model_has_examples(self):
        """It should include example values in the WishlistItem model"""
        resp = self.client.get("/api/swagger.json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        swagger_spec = resp.get_json()
        definitions = swagger_spec["definitions"]

        item_model = definitions["WishlistItem"]
        properties = item_model["properties"]

        # Check that examples exist
        self.assertIn("example", properties["product_id"])
        self.assertIn("example", properties["product_name"])
        self.assertIn("example", properties["prices"])

        # Verify example values are reasonable
        self.assertIsInstance(properties["product_id"]["example"], int)
        self.assertIsInstance(properties["product_name"]["example"], str)
        self.assertIsInstance(properties["prices"]["example"], (int, float))

    def test_add_item_with_empty_payload(self):
        """It should return 400 when payload is empty"""
        wishlist = self._create_wishlists(1)[0]
        headers = {
            "Content-Type": "application/json",
            "X-User-Id": wishlist.customer_id,
        }

        # Test with empty JSON object
        resp = self.client.post(
            f"{BASE_URL}/{wishlist.id}/items",
            json={},  # Empty but valid JSON
            headers=headers,
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_item_with_negative_product_id(self):
        """It should return 400 when product_id is negative or zero"""
        wishlist = self._create_wishlists(1)[0]
        headers = {
            "Content-Type": "application/json",
            "X-User-Id": wishlist.customer_id,
        }

        # Test with negative product_id
        payload = {
            "product_id": -5,
            "product_name": "Invalid Item",
            "prices": 10.00,
        }
        resp = self.client.post(
            f"{BASE_URL}/{wishlist.id}/items", json=payload, headers=headers
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(b"must be positive", resp.data)

        # Test with zero product_id
        payload["product_id"] = 0
        resp = self.client.post(
            f"{BASE_URL}/{wishlist.id}/items", json=payload, headers=headers
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_query_wishlists_by_name_only_without_customer_id(self):
        """It should return 400 when name is provided without customer_id"""
        # This test might already exist, but ensuring it's comprehensive
        resp = self.client.get(f"{BASE_URL}?name=test")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.get_json()
        self.assertIn("customer_id is required", data["message"].lower())

    def test_delete_wishlist_that_does_not_exist(self):
        """It should return 204 even when deleting non-existent wishlist (idempotent)"""
        headers = {"X-Api-Key": self.api_key}

        # Try to delete a wishlist that doesn't exist
        resp = self.client.delete(f"{BASE_URL}/99999", headers=headers)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_add_item_with_non_integer_product_id(self):
        """It should return 400 when product_id is not an integer type"""
        wishlist = self._create_wishlists(1)[0]
        headers = {
            "Content-Type": "application/json",
            "X-User-Id": wishlist.customer_id,
        }

        # Test with string product_id
        payload = {
            "product_id": "not_an_integer",
            "product_name": "Invalid Item",
            "prices": 10.00,
        }
        resp = self.client.post(
            f"{BASE_URL}/{wishlist.id}/items", json=payload, headers=headers
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(b"product_id must be an integer", resp.data)

    def test_add_item_with_empty_string_product_name(self):
        """It should return 400 when product_name is empty string or whitespace"""
        wishlist = self._create_wishlists(1)[0]
        headers = {
            "Content-Type": "application/json",
            "X-User-Id": wishlist.customer_id,
        }

        # Test with empty string
        payload = {
            "product_id": 123,
            "product_name": "",
            "prices": 10.00,
        }
        resp = self.client.post(
            f"{BASE_URL}/{wishlist.id}/items", json=payload, headers=headers
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(b"non-empty string", resp.data)

        # Test with whitespace only
        payload["product_name"] = "   "
        resp = self.client.post(
            f"{BASE_URL}/{wishlist.id}/items", json=payload, headers=headers
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_item_with_invalid_price_format(self):
        """It should return 400 when price is not a valid number"""
        wishlist = self._create_wishlists(1)[0]
        headers = {
            "Content-Type": "application/json",
            "X-User-Id": wishlist.customer_id,
        }

        # Test with invalid price (not a number)
        payload = {
            "product_id": 123,
            "product_name": "Test Item",
            "prices": "not_a_number",
        }
        resp = self.client.post(
            f"{BASE_URL}/{wishlist.id}/items", json=payload, headers=headers
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(b"price must be a number", resp.data)

    def test_list_items_for_nonexistent_wishlist(self):
        """It should return 404 when listing items for non-existent wishlist"""
        resp = self.client.get(f"{BASE_URL}/99999/items")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        data = resp.get_json()
        self.assertIn("not found", data["message"].lower())

    def test_get_item_from_nonexistent_wishlist(self):
        """It should return 404 when getting item from non-existent wishlist"""
        resp = self.client.get(f"{BASE_URL}/99999/items/1")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        data = resp.get_json()
        self.assertIn("wishlist", data["message"].lower())
        self.assertIn("not found", data["message"].lower())

    def test_get_nonexistent_item_from_existing_wishlist(self):
        """It should return 404 when item doesn't exist"""
        wishlist = self._create_wishlists(1)[0]

        # Try to get an item that doesn't exist
        resp = self.client.get(f"{BASE_URL}/{wishlist.id}/items/99999")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        data = resp.get_json()
        self.assertIn("item", data["message"].lower())
        self.assertIn("not found", data["message"].lower())

    def test_update_item_in_nonexistent_wishlist(self):
        """It should return 404 when updating item in non-existent wishlist"""
        payload = {"product_id": 123, "product_name": "Updated Item", "prices": 29.99}

        resp = self.client.put(f"{BASE_URL}/99999/items/1", json=payload)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_item_from_wrong_wishlist(self):
        """It should return 404 when item belongs to a different wishlist"""
        # Create two wishlists
        wishlists = self._create_wishlists(2)
        wishlist1 = wishlists[0]
        wishlist2 = wishlists[1]

        # Add an item to wishlist1
        item = ItemFactory(wishlist_id=wishlist1.id, customer_id=wishlist1.customer_id)
        item.create()

        # Try to GET the item using wishlist2's ID (wrong wishlist)
        resp = self.client.get(f"{BASE_URL}/{wishlist2.id}/items/{item.id}")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        data = resp.get_json()
        self.assertIn("not found", data["message"].lower())
