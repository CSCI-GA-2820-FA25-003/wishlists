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

    def test_create_wishlist_no_content_type(self):
        """It should return 415 when Content-Type header is missing"""
        wishlist = WishlistFactory()

        resp = self.client.post(
            BASE_URL,
            data=str(wishlist.serialize()),
        )

        self.assertEqual(resp.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
        data = resp.get_json()
        self.assertIn("Content-Type", data["message"])

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

        from service.models import Item

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

        from service.models import Item

        self.assertIsNotNone(Item.find(item.id))
