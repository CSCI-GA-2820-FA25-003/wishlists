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
