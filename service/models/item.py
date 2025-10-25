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
# pylint: disable=duplicate-code

import logging
from decimal import Decimal
from datetime import datetime
from .persistent_base import db, PersistentBase, DataValidationError


logger = logging.getLogger("flask.app")


######################################################################
#  I T E M   M O D E L
######################################################################
class Item(db.Model, PersistentBase):
    """
    Class that represents an Item
    """

    # Table Schema
    id = db.Column(db.Integer, primary_key=True)
    # Foreign Key -> wishlists.id  (make sure Wishlist.__tablename__ = "wishlists" and pk = id)
    wishlist_id = db.Column(
        db.Integer, db.ForeignKey("wishlist.id", ondelete="CASCADE"), nullable=False
    )
    # customer_id = db.Column(db.BigInteger, nullable=False)
    customer_id = db.Column(db.String(16), nullable=False)
    product_id = db.Column(db.BigInteger, nullable=False)
    product_name = db.Column(db.String(255), nullable=False)
    wish_date = db.Column(
        db.DateTime(timezone=True), server_default=db.func.now(), nullable=False
    )
    prices = db.Column(db.Numeric(10, 2), nullable=False)

    # Timestamps (PersistentBase may already add these; keep if your base doesn’t)
    created_at = db.Column(
        db.DateTime(timezone=True), server_default=db.func.now(), nullable=False
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )
    __table_args__ = (
        db.UniqueConstraint(
            "wishlist_id", "product_id", name="uq_item_wishlist_product"
        ),
    )

    def __repr__(self):
        return f"<WishlistItem id={self.id} wishlist={self.wishlist_id} product={self.product_id}>"

    def __str__(self):
        return f"wishlist[{self.wishlist_id}] product[{self.product_id}] {self.product_name}"

    def serialize(self) -> dict:
        """Converts an Item into a dictionary"""
        return {
            "id": self.id,
            "wishlist_id": self.wishlist_id,
            "customer_id": self.customer_id,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "wish_date": self.wish_date.isoformat() if self.wish_date else None,
            "prices": float(self.prices) if self.prices is not None else None,
        }

    def deserialize(self, data: dict) -> None:
        """
        Populates an Item from a dictionary

        Args:
            data (dict): A dictionary containing the resource data
        """
        try:
            # self.wishlist_id = data["wishlist_id"]
            # self.customer_id = data["customer_id"]
            self.product_id = data["product_id"]
            self.product_name = data["product_name"]
            wish_date_str = data.get("wish_date")
            if wish_date_str:
                self.wish_date = datetime.fromisoformat(wish_date_str)
            self.prices = data["prices"]

            if data["prices"] is not None:
                self.prices = Decimal(str(data["prices"]))
            else:
                self.prices = None
        except AttributeError as error:
            raise DataValidationError("Invalid attribute: " + error.args[0]) from error
        except KeyError as error:
            raise DataValidationError(
                "Invalid Item: missing " + error.args[0]
            ) from error
        except TypeError as error:
            raise DataValidationError(
                "Invalid Item: body of request contained bad or no data " + str(error)
            ) from error

        return self
