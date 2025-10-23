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
    base = request.host_url.rstrip("/")
    return (
        jsonify(
            name="Wishlist Service",
            version="1.0.0",
            description="RESTful service for managing wishlists",
            paths={
                # "wishlists": "/wishlists",
                # ----------- Wishlist endpoints -----------
                "list_all_wishlists": f"{base}/wishlists",
                "create_wishlist": f"{base}/wishlists",
                "get_wishlist": f"{base}/wishlists/{{wishlist_id}}",
                "update_wishlist": f"{base}/wishlists/{{wishlist_id}}",
                "delete_wishlist": f"{base}/wishlists/{{wishlist_id}}",
                # ----------- Wishlist Item endpoints -----------
                "list_wishlist_items": f"{base}/wishlists/{{wishlist_id}}/items",
                "create_wishlist_item": f"{base}/wishlists/{{wishlist_id}}/items",
                "get_wishlist_item": f"{base}/wishlists/{{wishlist_id}}/items/{{item_id}}",
                "update_wishlist_item": f"{base}/wishlists/{{wishlist_id}}/items/{{item_id}}",
                "delete_wishlist_item": f"{base}/wishlists/{{wishlist_id}}/items/{{item_id}}",
            },
        ),
        status.HTTP_200_OK,
    )


######################################################################
#  R E S T   A P I   E N D P O I N T S
######################################################################


######################################################################
# LIST ITEM
######################################################################
@app.route("/wishlists/<int:wishlist_id>/items", methods=["GET"])
def list_wishlist_item(wishlist_id: int):
    """Returns all of the Item for an Wishlists"""
    app.logger.info("Request for all Addresses for Account with id: %s", wishlist_id)

    # See if the account exists and abort if it doesn't
    wishlist = Wishlist.find(wishlist_id)
    if not wishlist:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Wishlist with id '{wishlist}' could not be found.",
        )

    # Get the addresses for the account
    results = [item.serialize() for item in wishlist.items]

    return jsonify(results), status.HTTP_200_OK


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
    # item = Item(
    #     wishlist_id=wishlist.id,
    #     customer_id=wishlist.customer_id,
    #     product_id=product_id,
    #     product_name=product_name,
    #     prices=price_val,
    # )
    item = Item()
    item.deserialize(
        {
            "wishlist_id": wishlist.id,
            "customer_id": wishlist.customer_id,
            "product_id": product_id,
            "product_name": product_name,
            "prices": price_val,
        }
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

    location_url = url_for("get_wishlists", wishlist_id=wishlist.id, _external=True)
    # location_url = "unknown"

    app.logger.info("Wishlist with id [%s] created.", wishlist.id)
    return jsonify(message), status.HTTP_201_CREATED, {"Location": location_url}


######################################################################
# DELETE A WISHLIST
######################################################################
@app.route("/wishlists/<int:wishlist_id>", methods=["DELETE"])
def delete_wishlists(wishlist_id: int):
    """Deletes a Wishlist by id"""
    app.logger.info("Request to delete Wishlist with id [%s]", wishlist_id)

    wishlist = Wishlist.find(wishlist_id)
    # if wishlist is None:
    #     abort(
    #         status.HTTP_404_NOT_FOUND,
    #         f"Wishlist with id '{wishlist_id}' was not found.",
    #     )
    if wishlist:
        wishlist.delete()

    app.logger.info("Wishlist with id [%s] deleted", wishlist_id)
    return "", status.HTTP_204_NO_CONTENT


######################################################################
# DELETE A WISHLIST ITEM
######################################################################
@app.route("/wishlists/<int:wishlist_id>/items/<int:item_id>", methods=["DELETE"])
def delete_wishlist_items(wishlist_id: int, item_id: int):
    """
    Idempotently delete an Item from a Wishlist.
    Always return 204, even if the item does not exist or does not belong to the wishlist.
    """
    app.logger.info(
        "Request to delete Item [%s] from Wishlist [%s]", item_id, wishlist_id
    )

    item = Item.find(item_id)

    if item and item.wishlist_id == wishlist_id:
        item.delete()
        app.logger.info("Item [%s] deleted from Wishlist [%s]", item_id, wishlist_id)
    else:
        app.logger.info(
            "Item [%s] not present in Wishlist [%s]; returning 204 (idempotent)",
            item_id,
            wishlist_id,
        )

    return "", status.HTTP_204_NO_CONTENT


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
# UPDATE A WISHLIST ITEM
######################################################################
@app.route("/wishlists/<int:wishlist_id>/items/<int:item_id>", methods=["PUT"])
def update_wishlist_items(wishlist_id, item_id):
    """
    Update a Wishlist Item
    This endpoint will update an Item in a Wishlist
    """
    app.logger.info("Request to update Item %s in Wishlist %s", item_id, wishlist_id)
    check_content_type("application/json")

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

    # Update the item with the request data
    item.deserialize(request.get_json())
    item.update()

    app.logger.info("Item with id [%s] updated.", item.id)
    return jsonify(item.serialize()), status.HTTP_200_OK


######################################################################
# LIST ALL wishlists
######################################################################
@app.route("/wishlists", methods=["GET"])
def list_wishlists():
    """Returns all of the Accounts"""
    app.logger.info("Request for Wishlists list")
    wishlists = []

    # Process the query string if any
    customer_id = request.args.get("customer_id")
    if customer_id:
        wishlists = Wishlist.find_by_customer(customer_id)
    else:
        wishlists = Wishlist.all()

    # Return as an array of dictionaries
    results = [wishlist.serialize() for wishlist in wishlists]

    return jsonify(results), status.HTTP_200_OK


#################################################################
# UPDATE A WISHLIST
######################################################################
@app.route("/wishlists/<int:wishlist_id>", methods=["PUT"])
def update_wishlists(wishlist_id: int):
    """Updates an existing wishlist's name or description and returns 200 OK."""
    check_content_type("application/json")

    # Check exist
    wishlist = Wishlist.find(wishlist_id)
    if not wishlist:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Wishlist with id '{wishlist_id}' was not found.",
        )

    # Check Ownership
    if request.headers.get("X-Customer-Id") != wishlist.customer_id:
        abort(status.HTTP_403_FORBIDDEN, "You do not own this wishlist")

    # Partial Updates
    data = request.get_json() or {}
    if "name" in data:
        wishlist.name = data["name"]
    if "description" in data:
        wishlist.description = data["description"]

    wishlist.update()
    return jsonify(wishlist.serialize()), status.HTTP_200_OK


#################################################################
# CLEAR A WISHLIST
#################################################################
@app.route("/wishlists/<int:wishlist_id>/clear", methods=["PUT"])
def clear_wishlist(wishlist_id: int):
    """
    Clear all items in the given Wishlist (idempotent).
    Responses:
        204 No Content: wishlist cleared successfully (even if it was already empty)
        404 Not Found : wishlist does not exist
    """
    app.logger.info("Request to clear all items in Wishlist [%s]", wishlist_id)

    wishlist = Wishlist.find(wishlist_id)
    if not wishlist:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Wishlist with id '{wishlist_id}' was not found.",
        )

    deleted = wishlist.clear_items()  # domain method commits the transaction
    app.logger.info(
        "Cleared %s item(s) from Wishlist [%s] (idempotent 204).",
        deleted,
        wishlist_id,
    )
    return "", status.HTTP_204_NO_CONTENT


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
