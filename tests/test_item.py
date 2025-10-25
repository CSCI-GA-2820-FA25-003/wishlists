"""
Test cases for Item Model
"""

import logging
import os
from unittest import TestCase
from wsgi import app
from service.models import Item, Wishlist, db, DataValidationError
from tests.factories import WishlistFactory, ItemFactory

# pylint: disable=duplicate-code
DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#        I T E M   M O D E L   T E S T   C A S E S
######################################################################
class TestWishlist(TestCase):
    """Item Model Test Cases"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        app.app_context().push()

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Item).delete()  # clean up the last tests
        db.session.query(Wishlist).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################
    def test_add_wishlist_item(self):
        """It should Create a wishlist with an item and add it to the database"""
        wishlists = Wishlist.all()
        self.assertEqual(wishlists, [])

        wishlist = WishlistFactory()
        item = ItemFactory(wishlist=wishlist)

        # attach and persist
        wishlist.items.append(item)
        wishlist.create()

        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(wishlist.id)
        wishlists = Wishlist.all()
        self.assertEqual(len(wishlists), 1)

        new_wishlist = Wishlist.find(wishlist.id)
        self.assertEqual(len(new_wishlist.items), 1)
        self.assertEqual(new_wishlist.items[0].product_name, item.product_name)

        # add another item
        item2 = ItemFactory(wishlist=wishlist)
        new_wishlist.items.append(item2)
        new_wishlist.update()

        again = Wishlist.find(wishlist.id)
        self.assertEqual(len(again.items), 2)
        self.assertEqual(again.items[1].product_name, item2.product_name)

    def test_update_wishlist_item(self):
        """It should Update a wishlist item"""
        wishlists = Wishlist.all()
        self.assertEqual(wishlists, [])

        wishlist = WishlistFactory()
        item = ItemFactory(wishlist=wishlist)
        wishlist.items.append(item)
        wishlist.create()

        # Assert persisted
        self.assertIsNotNone(wishlist.id)
        wishlists = Wishlist.all()
        self.assertEqual(len(wishlists), 1)

        # Fetch it back
        wishlist = Wishlist.find(wishlist.id)
        old_item = wishlist.items[0]
        self.assertEqual(old_item.product_name, item.product_name)

        # Change the product_name (or prices)
        old_item.product_name = "updated-name"
        wishlist.update()

        # Fetch it back again
        wishlist = Wishlist.find(wishlist.id)
        item = wishlist.items[0]
        self.assertEqual(item.product_name, "updated-name")

    def test_delete_wishlist_item(self):
        """It should Delete a wishlist item"""
        wishlists = Wishlist.all()
        self.assertEqual(wishlists, [])

        wishlist = WishlistFactory()
        item = ItemFactory(wishlist=wishlist)
        wishlist.items.append(item)
        wishlist.create()

        # Assert persisted
        self.assertIsNotNone(wishlist.id)
        wishlists = Wishlist.all()
        self.assertEqual(len(wishlists), 1)

        # Fetch it back
        wishlist = Wishlist.find(wishlist.id)
        item = wishlist.items[0]
        item.delete()
        wishlist.update()

        # Fetch it back again
        wishlist = Wishlist.find(wishlist.id)
        self.assertEqual(len(wishlist.items), 0)

    def test_serialize_an_item(self):
        """It should serialize an Item"""
        item = ItemFactory()
        serial_item = item.serialize()

        self.assertEqual(serial_item["id"], item.id)
        self.assertEqual(serial_item["wishlist_id"], item.wishlist_id)
        self.assertEqual(serial_item["customer_id"], item.customer_id)
        self.assertEqual(serial_item["product_id"], item.product_id)
        self.assertEqual(serial_item["product_name"], item.product_name)
        self.assertIn("wish_date", serial_item)
        self.assertIn("prices", serial_item)

    def test_deserialize_an_item(self):
        """It should deserialize an Item"""
        item = ItemFactory()
        item.create()

        new_item = Item()
        new_item.deserialize(item.serialize())

        # self.assertEqual(new_item.wishlist_id, item.wishlist_id)
        # self.assertEqual(new_item.customer_id, item.customer_id)
        self.assertEqual(new_item.product_id, item.product_id)
        self.assertEqual(new_item.product_name, item.product_name)
        self.assertEqual(new_item.prices, item.prices)

    def test_deserialize_item_with_null_price(self):
        """It should deserialize an Item with a null price"""
        data = {"product_id": 123, "product_name": "Test Item", "prices": None}
        item = Item()
        item.deserialize(data)

        self.assertEqual(item.product_id, 123)
        self.assertIsNone(item.prices)

    def test_item_str_and_repr(self):
        """It should render __str__ and __repr__ correctly"""
        wl = WishlistFactory()
        it = ItemFactory(wishlist=wl)
        # __str__
        s = str(it)
        self.assertIn(f"wishlist[{it.wishlist_id}]", s)
        self.assertIn(f"product[{it.product_id}]", s)
        self.assertIn(it.product_name, s)
        # __repr__
        r = repr(it)
        self.assertIn("WishlistItem", r)
        self.assertIn(f"id={it.id}", r)
        self.assertIn(f"wishlist={it.wishlist_id}", r)
        self.assertIn(f"product={it.product_id}", r)

    def test_item_deserialize_attribute_error(self):
        """It should raise DataValidationError on AttributeError in Item.deserialize"""

        class FakeMapping:  # pylint: disable=too-few-public-methods
            """Minimal mapping to trigger AttributeError in Item.deserialize."""

            def __getitem__(self, key):
                base = {
                    "wishlist_id": 101,
                    "customer_id": "User0001",
                    "product_id": 67890,
                    "product_name": "iPhone",
                    "prices": 999.00,
                }
                if key in base:
                    return base[key]
                raise KeyError(key)

        it = Item()
        self.assertRaises(DataValidationError, it.deserialize, FakeMapping())
