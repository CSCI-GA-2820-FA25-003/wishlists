"""
Test cases for Item Model
"""

import logging
import os
from unittest import TestCase
from wsgi import app
from service.models import Item, Wishlist, db
from tests.factories import WishlistFactory, ItemFactory

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
