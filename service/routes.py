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
Wishlist Service

This service implements a REST API that allows you to Create, Read, Update
and Delete Wishlist
"""

from flask import jsonify, request, url_for, abort
from flask import current_app as app  # Import Flask application
from service.models import Wishlist, Item
from service.common import status  # HTTP Status Codes


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Root URL response"""
    return (
        jsonify(
            name="Wishlist Service",
            version="1.0.0",
            description="RESTful service for managing wishlists",
            paths={
                "wishlists": "/wishlists",
            },
        ),
        status.HTTP_200_OK,
    )


######################################################################
#  R E S T   A P I   E N D P O I N T S
######################################################################
# Todo: Place your REST API code here ...


######################################################################
# ADD AN ITEM TO A WISHLIST
######################################################################
@app.route("/wishlists/<int:wishlist_id>/items", methods=["POST"])
def add_wishlist_item(wishlist_id: int):
    """
    Adds a product Item to a Wishlist

    Expects JSON body with: product_id (int), product_name (str), price (number)
    Optional: description (ignored by current data model)

    Duplicate prevention on (wishlist_id, product_id).
    Note: Authentication/authorization is intentionally not handled here and is
    expected to be enforced by upstream services (e.g., API Gateway).
    """
    app.logger.info("Request to add Item to Wishlist %s", wishlist_id)
    check_content_type("application/json")

    # Ensure wishlist exists
    wishlist = Wishlist.find(wishlist_id)
    if not wishlist:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Wishlist with id '{wishlist_id}' was not found.",
        )

    # No ownership/auth checks in this service per product decision

    payload = request.get_json() or {}

    # Validate required fields
    missing = [f for f in ("product_id", "product_name", "price") if f not in payload]
    if missing:
        abort(
            status.HTTP_400_BAD_REQUEST,
            f"Invalid request: missing required field(s): {', '.join(missing)}",
        )

    # product_id validation
    product_id = payload.get("product_id")
    if not isinstance(product_id, int):
        abort(status.HTTP_400_BAD_REQUEST, "product_id must be an integer")
    if product_id <= 0:
        abort(status.HTTP_400_BAD_REQUEST, "Invalid product_id: must be positive")

    # product_name validation (basic)
    product_name = payload.get("product_name")
    if not isinstance(product_name, str) or not product_name.strip():
        abort(status.HTTP_400_BAD_REQUEST, "product_name must be a non-empty string")

    # price snapshot
    price = payload.get("price")
    try:
        price_val = float(price)
    except Exception:  # pylint: disable=broad-except
        abort(status.HTTP_400_BAD_REQUEST, "price must be a number")

    # Duplicate prevention
    existing = Item.query.filter_by(
        wishlist_id=wishlist_id, product_id=product_id
    ).first()
    if existing:
        abort(
            status.HTTP_409_CONFLICT,
            f"Item with product_id '{product_id}' already exists in this wishlist.",
        )

    # Create and persist the item
    item = Item(
        wishlist_id=wishlist.id,
        customer_id=wishlist.customer_id,
        product_id=product_id,
        product_name=product_name,
        prices=price_val,
    )
    item.create()

    # Refetch to ensure server defaults (wish_date) are populated
    item = Item.find(item.id)

    location_url = url_for(
        "get_wishlist_items", wishlist_id=wishlist.id, item_id=item.id, _external=True
    )
    app.logger.info("Item %s added to Wishlist %s", item.id, wishlist.id)
    return (
        jsonify(item.serialize()),
        status.HTTP_201_CREATED,
        {"Location": location_url},
    )


######################################################################
# CREATE A NEW WISHLIST
######################################################################
@app.route("/wishlists", methods=["POST"])
def create_wishlists():
    """
    Creates a Wishlist
    This endpoint will create a Wishlist based on the JSON body provided
    """
    app.logger.info("Request to create a Wishlist")
    check_content_type("application/json")

    # Create the wishlist
    wishlist = Wishlist()
    wishlist.deserialize(request.get_json())
    wishlist.create()

    # Create a message to return
    message = wishlist.serialize()

    # Todo: uncomment this code when get_wishlists is implemented
    location_url = url_for("get_wishlists", wishlist_id=wishlist.id, _external=True)
    # location_url = "unknown"

    app.logger.info("Wishlist with id [%s] created.", wishlist.id)
    return jsonify(message), status.HTTP_201_CREATED, {"Location": location_url}


######################################################################
# READ A WISHLIST
######################################################################
@app.route("/wishlists/<int:wishlist_id>", methods=["GET"])
def get_wishlists(wishlist_id):
    """
    Retrieve a single Wishlist
    This endpoint will return a Wishlist based on its id
    """
    app.logger.info("Request to Retrieve a wishlist with id [%s]", wishlist_id)

    # Attempt to find the Wishlist and abort if not found
    wishlist = Wishlist.find(wishlist_id)
    if not wishlist:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Wishlist with id '{wishlist_id}' was not found.",
        )

    app.logger.info("Returning wishlist: %s", wishlist.name)
    return jsonify(wishlist.serialize()), status.HTTP_200_OK


######################################################################
# READ A WISHLIST ITEM
######################################################################
@app.route("/wishlists/<int:wishlist_id>/items/<int:item_id>", methods=["GET"])
def get_wishlist_items(wishlist_id, item_id):
    """
    Retrieve a single Item from a Wishlist
    This endpoint will return an Item based on its id
    """
    app.logger.info(
        "Request to retrieve Item %s from Wishlist %s", item_id, wishlist_id
    )

    # First check if the wishlist exists
    wishlist = Wishlist.find(wishlist_id)
    if not wishlist:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Wishlist with id '{wishlist_id}' was not found.",
        )

    # Then check if the item exists
    item = Item.find(item_id)
    if not item:
        abort(status.HTTP_404_NOT_FOUND, f"Item with id '{item_id}' was not found.")

    # Verify the item belongs to this wishlist
    if item.wishlist_id != wishlist_id:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Item with id '{item_id}' was not found in Wishlist '{wishlist_id}'.",
        )

    app.logger.info("Returning item: %s", item.product_name)
    return jsonify(item.serialize()), status.HTTP_200_OK


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################


def check_content_type(content_type):
    """Checks that the media type is correct"""
    if "Content-Type" not in request.headers:
        app.logger.error("No Content-Type specified.")
        abort(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Content-Type must be {content_type}",
        )

    if request.headers["Content-Type"] == content_type:
        return

    app.logger.error("Invalid Content-Type: %s", request.headers["Content-Type"])
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, f"Content-Type must be {content_type}"
    )
