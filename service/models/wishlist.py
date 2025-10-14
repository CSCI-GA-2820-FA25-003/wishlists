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
Persistent Base class for database CRUD functions
"""

import logging

# from datetime import date
from .persistent_base import db, PersistentBase, DataValidationError
from .item import Item

logger = logging.getLogger("flask.app")


######################################################################
#  W I S H L I S T   M O D E L
######################################################################
class Wishlist(db.Model, PersistentBase):
    """
    Class that represents an Wishlist
    """

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)  # expose as wishlist_id in serialize()

    # Business fields
    # customer_id = db.Column(db.BigInteger, nullable=False)
    customer_id = db.Column(db.String(16), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(500))

    # Timestamps (PersistentBase may already supply; keep if your base doesn’t)
    created_at = db.Column(
        db.DateTime(timezone=True), server_default=db.func.now(), nullable=False
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )

    # Relationship: one wishlist has many items
    items = db.relationship(
        "Item",
        backref="wishlist",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    __table_args__ = (
        db.UniqueConstraint("customer_id", "name", name="uq_wishlist_customer_name"),
    )

    def __repr__(self):
        return f"<Wishlist {self.name} id=[{self.id}] customer=[{self.customer_id}]>"

    def serialize(self):
        """Converts an Wishlist into a dictionary"""
        wishlist = {
            "id": self.id,
            "customer_id": self.customer_id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "items": [],
        }
        for item in self.items:
            wishlist["items"].append(item.serialize())
        return wishlist

    def deserialize(self, data):
        """
        Populates an Wishlist from a dictionary

        Args:
            data (dict): A dictionary containing the resource data
        """
        try:
            self.customer_id = data["customer_id"]
            self.name = data["name"]
            self.description = data.get("description")

            # handle inner list of items
            item_list = data.get("items", [])
            for json_item in item_list:
                item = Item()
                self.items.append(item)
                item.deserialize(json_item)

        except AttributeError as error:
            raise DataValidationError("Invalid attribute: " + error.args[0]) from error
        except KeyError as error:
            raise DataValidationError(
                "Invalid Wishlist: missing " + error.args[0]
            ) from error
        except TypeError as error:
            raise DataValidationError(
                "Invalid Wishlist: body of request contained bad or no data "
                + str(error)
            ) from error

        return self

    ######################################################################
    #  CLASS METHODS
    ######################################################################
    @classmethod
    def all(cls) -> list:
        """
        Retrieves all Wishlists from the database.

        :return: A list of all Wishlist objects found.
        :rtype: list[Wishlist]
        """
        logger.info("Processing all Wishlists")
        return cls.query.all()

    @classmethod
    def find_by_name(cls, name):
        """Returns all Wishlists with the given name

        Args:
            name (string): the name of the Wishlists you want to match
        """
        logger.info("Processing name query for %s ...", name)
        return cls.query.filter(cls.name == name)

    @classmethod
    def find_by_customer(cls, customer_id):
        """Returns all Wishlists owned by a given customer"""
        logger.info("Processing customer query for %s ...", customer_id)
        return cls.query.filter(cls.customer_id == customer_id)
