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
from service.models import db, Wishlist

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/postgres"
)
BASE_URL = "/wishlists"


######################################################################
#  T E S T   C A S E S
######################################################################
class TestWishlistService(TestCase):
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

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  P L A C E   T E S T   C A S E S   H E R E
    ######################################################################

    def test_index(self):
        """It should call the home page"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["name"], "Wishlist Service")
        self.assertEqual(data["version"], "1.0.0")
        self.assertEqual(data["description"], "RESTful service for managing wishlists")
        self.assertIn("wishlists", data["paths"])

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_wishlists(self, count):
        """Factory method to create wishlists in bulk"""
        wishlists = []
        for _ in range(count):
            wishlist = WishlistFactory()
            resp = self.client.post(BASE_URL, json=wishlist.serialize())
            self.assertEqual(
                resp.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Wishlist",
            )
            new_wishlist = resp.get_json()
            wishlist.id = new_wishlist["id"]
            wishlists.append(wishlist)
        return wishlists

    ######################################################################
    #  W I S H L I S T   T E S T   C A S E S
    ######################################################################

    def test_create_wishlist(self):
        """It should Create a new Wishlist"""
        wishlist = WishlistFactory()
        resp = self.client.post(
            BASE_URL, json=wishlist.serialize(), content_type="application/json"
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
        self.assertEqual(new_wishlist["items"], wishlist.items, "Items do not match")

        # Todo: Uncomment this code when get_wishlists is implemented

        # Check that the location header was correct by getting it
        resp = self.client.get(location, content_type="application/json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
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
        self.assertEqual(new_wishlist["items"], wishlist.items, "Items do not match")

    def test_create_wishlist_bad_payload(self):
        """It should fail with 400 BAD_REQUEST when request body is missing required fields"""
        resp = self.client.post(
            "/wishlists",
            json={"description": "only desc"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.get_json()
        self.assertEqual(data["status"], status.HTTP_400_BAD_REQUEST)
        self.assertIn("Bad Request", data["error"])

    def test_create_wishlist_method_not_allowed(self):
        """It should return 405 METHOD_NOT_ALLOWED when using an unsupported HTTP method"""
        resp = self.client.put("/wishlists", json={})
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        data = resp.get_json()
        self.assertEqual(data["status"], status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_create_wishlist_wrong_content_type(self):
        """It should fail with 415 UNSUPPORTED_MEDIA_TYPE when Content-Type is not application/json"""
        resp = self.client.post("/wishlists", data="{}", content_type="text/html")
        self.assertEqual(resp.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
        data = resp.get_json()
        self.assertEqual(data["status"], status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_delete_wishlist_success(self):
        """It should delete a Wishlist and return 204 NO_CONTENT"""
        # Create a wishlist first
        wishlist = WishlistFactory()
        resp = self.client.post(
            BASE_URL, json=wishlist.serialize(), content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        wishlist_id = resp.get_json()["id"]

        # Sanity: it exists in DB
        self.assertIsNotNone(Wishlist.find(wishlist_id))

        # Delete it
        resp = self.client.delete(f"{BASE_URL}/{wishlist_id}")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        # No response body for 204
        self.assertEqual(resp.data, b"")

        # Verify removed from DB
        self.assertIsNone(Wishlist.find(wishlist_id))

    def test_delete_wishlist_not_found(self):
        """It should return 404 NOT_FOUND when deleting a non-existent Wishlist"""
        resp = self.client.delete(f"{BASE_URL}/0")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        data = resp.get_json()
        self.assertEqual(data["status"], status.HTTP_404_NOT_FOUND)
        self.assertIn("Not Found", data["error"])
        
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

    ######################################################################
    #  I T E M   T E S T   C A S E S
    ######################################################################

    def test_get_wishlist_item(self):
        """It should Get a single Item from a Wishlist"""
        # Create a wishlist with an item
        wishlist = WishlistFactory()
        item = ItemFactory(wishlist=wishlist)
        wishlist.items.append(item)
        wishlist.create()

        # Retrieve the item
        response = self.client.get(f"{BASE_URL}/{wishlist.id}/items/{item.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.get_json()
        self.assertEqual(data["id"], item.id)
        self.assertEqual(data["product_id"], item.product_id)
        self.assertEqual(data["product_name"], item.product_name)
        self.assertEqual(data["wishlist_id"], wishlist.id)

    def test_get_wishlist_item_not_found(self):
        """It should not Get an Item that doesn't exist"""
        # Create a wishlist without items
        wishlist = self._create_wishlists(1)[0]

        # Try to get non-existent item
        response = self.client.get(f"{BASE_URL}/{wishlist.id}/items/0")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.get_json()
        self.assertIn("was not found", data["message"])

    def test_get_item_wishlist_not_found(self):
        """It should not Get an Item if Wishlist doesn't exist"""
        response = self.client.get(f"{BASE_URL}/0/items/1")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.get_json()
        self.assertIn("Wishlist", data["message"])

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
            "price": 19.99,
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
        self.assertAlmostEqual(data["prices"], payload["price"], places=2)

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
        payload = {"product_id": 98765, "product_name": "gadget", "price": 9.99}

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

    ######################################################################
    #  E R R O R   H A N D L E R   T E S T S
    ######################################################################

    def test_error_handler_forbidden(self):
        """It should return a JSON 403 response from the forbidden error handler"""
        from service.common.error_handlers import forbidden

        resp, code = forbidden(Exception("forbidden test"))
        self.assertEqual(code, status.HTTP_403_FORBIDDEN)
        data = resp.get_json()
        self.assertEqual(data["status"], status.HTTP_403_FORBIDDEN)
        self.assertEqual(data["error"], "Forbidden")
        self.assertIn("forbidden test", data["message"])

    def test_error_handler_internal_server_error(self):
        """It should return a JSON 500 response from the internal server error handler"""
        from service.common.error_handlers import internal_server_error

        resp, code = internal_server_error(Exception("boom"))
        self.assertEqual(code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        data = resp.get_json()
        self.assertEqual(data["status"], status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(data["error"], "Internal Server Error")
        self.assertIn("boom", data["message"])
