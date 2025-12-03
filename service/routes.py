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
Wishlist Service with Swagger


Paths:
------
GET / - Displays a UI for Selenium testing
GET /wishlists - Returns a list all of the Wishlists
GET /wishlists/{id} - Returns the Wishlist with a given id number
POST /wishlists - creates a new Wishlist record in the database
PUT /wishlists/{id} - updates a Wishlist record in the database
DELETE /wishlists/{id} - deletes a Wishlist record in the database
"""
import secrets
from functools import wraps
from decimal import Decimal
from flask import jsonify, request, url_for, abort
from flask import current_app as app  # Import Flask application
from flask_restx import Api, Resource, fields, reqparse
from service.models import Wishlist, Item
from service.common import status  # HTTP Status Codes


# Document the type of authorization required
authorizations = {"apikey": {"type": "apiKey", "in": "header", "name": "X-Api-Key"}}

######################################################################
# Configure Swagger before initializing it
######################################################################
api = Api(
    app,
    version="1.0.0",
    title="Wishlist REST API Service",
    description="RESTful service for managing wishlists.",
    default="wishlists",
    default_label="Wishlist operations",
    doc="/apidocs",  # default also could use doc='/apidocs/'
    authorizations=authorizations,
    prefix="/api",
)


######################################################################
# Configure the Root route before OpenAPI
######################################################################
@app.route("/")
def index():
    """Return the Admin UI page"""
    return app.send_static_file("index.html")


# Define the model so that the docs reflect what can be sent
create_model = api.model(
    "Wishlist",
    {
        "name": fields.String(),
        "customer_id": fields.String(),
        "description": fields.String(),
    },
)

wishlist_model = api.inherit(
    "WishlistModel",
    create_model,
    {
        "id": fields.Integer(readOnly=True),
    },
)
wishlist_args = reqparse.RequestParser()
# query string arguments
wishlist_args.add_argument(
    "name", type=str, location="args", required=False, help="Filter Wishlists by name"
)

wishlist_args.add_argument(
    "customer_id",
    type=str,
    location="args",
    required=False,
    help="Filter Wishlists by customer_id",
)


######################################################################
# Authorization Decorator
######################################################################
def token_required(func):
    """Decorator to require a token for this endpoint"""

    @wraps(func)
    def decorated(*args, **kwargs):
        token = None
        if "X-Api-Key" in request.headers:
            token = request.headers["X-Api-Key"]

        if app.config.get("API_KEY") and app.config["API_KEY"] == token:
            return func(*args, **kwargs)

        return {"message": "Invalid or missing token"}, 401

    return decorated


######################################################################
# Function to generate a random API key (good for testing)
######################################################################
def generate_apikey():
    """Helper function used when testing API keys"""
    return secrets.token_hex(16)


############################################################
# Health Endpoint
############################################################
@app.route("/health")
def health():
    """Health Status"""
    return {"status": "OK"}, status.HTTP_200_OK


######################################################################
# GET API INDEX
######################################################################
@app.route("/api-info")
def api_index():
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
                # ----------- Action endpoints -----------
                "clear_wishlist": f"{base}/wishlists/{{wishlist_id}}/clear",
                "share_wishlist": f"{base}/wishlists/{{wishlist_id}}/share",
            },
        ),
        status.HTTP_200_OK,
    )


######################################################################
#  R E S T   A P I   E N D P O I N T S
######################################################################


######################################################################
#  PATH: /wishlists/{id}
######################################################################
@api.route("/wishlists/<wishlist_id>")
@api.param("wishlist_id", "The Wishlist identifier")
class WishlistResource(Resource):
    """
    WishlistResource class

    Allows the manipulation of a single wishlist
    GET /wishlist{id} - Returns a Wishlist with the id
    PUT /wishlist{id} - Update a Wishlist with the id
    DELETE /wishlist{id} -  Deletes a Wishlist with the id
    """

    # ------------------------------------------------------------------
    # RETRIEVE A Wishlist
    # ------------------------------------------------------------------
    @api.doc("get_wishlists")
    @api.response(404, "Wishlist not found")
    @api.marshal_with(wishlist_model)
    def get(self, wishlist_id):
        """
        Retrieve a single Wishlist

        This endpoint will return a Wishlist based on it's id
        """
        app.logger.info("Request to Retrieve a wishlist with id [%s]", wishlist_id)
        wishlist = Wishlist.find(wishlist_id)
        if not wishlist:
            abort(
                status.HTTP_404_NOT_FOUND,
                f"Wishlist with id '{wishlist_id}' was not found.",
            )

        app.logger.info("Returning wishlist: %s", wishlist.name)
        return wishlist.serialize(), status.HTTP_200_OK

    # ------------------------------------------------------------------
    # UPDATE AN EXISTING Wishlist
    # ------------------------------------------------------------------
    @api.doc("update_wishlists", security="apikey")
    @api.response(404, "Wishlist not found")
    @api.response(400, "The posted Wishlist data was not valid")
    @api.expect(wishlist_model)
    @api.marshal_with(wishlist_model)
    @token_required
    def put(self, wishlist_id):
        """
        Updates an existing wishlist's name or description and returns 200 OK.
        """
        app.logger.info("Request to Update a wishlist with id [%s]", wishlist_id)
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
        app.logger.debug("Payload = %s", api.payload)
        # Partial Updates
        data = api.payload
        if "name" in data:
            wishlist.name = data["name"]
        if "description" in data:
            wishlist.description = data["description"]

        wishlist.update()
        return wishlist.serialize(), status.HTTP_200_OK

    # ------------------------------------------------------------------
    # DELETE A Wishlist
    # ------------------------------------------------------------------
    @api.doc("delete_wishlists", security="apikey")
    @api.response(204, "Wishlist deleted")
    @token_required
    def delete(self, wishlist_id):
        """
        Delete a Wishlist

        This endpoint will delete a Wishlist based the id specified in the path
        """
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
#  PATH: /wishlists
######################################################################
@api.route("/wishlists", strict_slashes=False)
class WishlistCollection(Resource):
    """Handles all interactions with collections of Wishlists"""

    # ------------------------------------------------------------------
    # LIST ALL Wishlists
    # ------------------------------------------------------------------
    @api.doc("list_wishlists")
    @api.expect(wishlist_args, validate=True)
    @api.marshal_list_with(wishlist_model)
    def get(self):
        """Returns all of the Wishlists with optional query parameters"""
        app.logger.info("Request for Wishlists list")
        # to examine query parameters
        args = wishlist_args.parse_args()
        name = args["name"]
        customer_id = args["customer_id"]

        # ADDED: Validate that name requires customer_id
        if name and not customer_id:
            app.logger.warning("name parameter requires customer_id")
            return abort(
                status.HTTP_400_BAD_REQUEST,
                "customer_id is required when querying by name",
            )

        wishlists = []
        # Process the query string if any
        if customer_id and name:
            # ADDED: Filter by both customer_id and name (substring, case-insensitive)
            app.logger.info(
                "Filtering by customer_id: %s and name: %s", customer_id, name
            )
            query_results = Wishlist.find_by_customer(customer_id)
            # Perform case-insensitive substring match
            wishlists = [wl for wl in query_results if name.lower() in wl.name.lower()]
        elif customer_id:
            app.logger.info("Filtering by customer_id: %s", customer_id)
            wishlists = Wishlist.find_by_customer(customer_id)
        elif name:
            app.logger.info("Filtering by name: %s", name)
            all_lists = Wishlist.all()
            wishlists = [wl for wl in all_lists if name.lower() in wl.name.lower()]
        else:
            app.logger.info("Return all wishlists")
            wishlists = Wishlist.all()

        # Return as an array of dictionaries
        results = [wishlist.serialize() for wishlist in wishlists]

        return results, status.HTTP_200_OK

    # ------------------------------------------------------------------
    # ADD A NEW Wishlist
    # ------------------------------------------------------------------
    @api.doc("create_wishlists", security="apikey")
    @api.response(400, "The posted data was not valid")
    @api.expect(create_model)
    @api.marshal_with(wishlist_model, code=201)
    @token_required
    def post(self):
        """
        Creates a Wishlist
        This endpoint will create a Wishlist based the data in the body that is posted
        """
        app.logger.info("Request to create a Wishlist")

        # Create the wishlist
        wishlist = Wishlist()
        app.logger.debug("Payload = %s", api.payload)
        wishlist.deserialize(api.payload)
        wishlist.create()
        app.logger.info("Wishlist with id [%s] created.", wishlist.id)
        location_url = api.url_for(
            WishlistResource, wishlist_id=wishlist.id, _external=True
        )

        return wishlist.serialize(), status.HTTP_201_CREATED, {"Location": location_url}


######################################################################
# LIST ITEM
######################################################################
@app.route("/api//wishlists/<int:wishlist_id>/items", methods=["GET"])
def list_wishlist_item(wishlist_id: int):
    """List Items in a Wishlist with optional filtering by product_id."""
    app.logger.info(
        "Request to list items for Wishlist id: %s with args: %s",
        wishlist_id,
        dict(request.args),
    )

    # Ensure the wishlist exists
    wishlist = Wishlist.find(wishlist_id)
    if not wishlist:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Wishlist with id '{wishlist_id}' was not found.",
        )

    # Validate query parameters
    params = request.args.to_dict(flat=True)
    allowed = {"product_id", "product_name"}
    unknown = set(params) - allowed
    if unknown:
        abort(
            status.HTTP_400_BAD_REQUEST,
            f"Unsupported query parameter(s): {', '.join(sorted(unknown))}. "
            "Supported: product_id, product_name",
        )

    items = wishlist.items

    # Optional filtering by product_id (exact integer)
    if "product_id" in params:
        try:
            pid = int(params["product_id"])
        except (TypeError, ValueError):
            abort(status.HTTP_400_BAD_REQUEST, "product_id must be an integer")
        items = [it for it in items if it.product_id == pid]

    # ---- NEW: Optional filtering by product_name (case-insensitive substring) ----
    if "product_name" in params and params["product_name"].strip():
        needle = params["product_name"].strip().lower()
        items = [it for it in items if needle in (it.product_name or "").lower()]

    results = [item.serialize() for item in items]
    return jsonify(results), status.HTTP_200_OK


######################################################################
# ADD AN ITEM TO A WISHLIST
######################################################################
@app.route("/api/wishlists/<int:wishlist_id>/items", methods=["POST"])
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
        price_val = Decimal(str(price))
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
    # item = Item()
    # item.deserialize(
    #     {
    #         "wishlist_id": wishlist.id,
    #         "customer_id": wishlist.customer_id,
    #         "product_id": product_id,
    #         "product_name": product_name,
    #         "prices": price_val,
    #     }
    # )
    item = Item()
    item.wishlist_id = wishlist.id
    item.customer_id = wishlist.customer_id
    item.product_id = product_id
    item.product_name = product_name
    item.prices = price_val
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
# DELETE A WISHLIST ITEM
######################################################################
@app.route("/api/wishlists/<int:wishlist_id>/items/<int:item_id>", methods=["DELETE"])
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


#################################################################
# CLEAR A WISHLIST item
#################################################################
@app.route("/api/wishlists/<int:wishlist_id>/clear", methods=["PUT"])
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
# UPDATE A WISHLIST ITEM
######################################################################
@app.route("/api/wishlists/<int:wishlist_id>/items/<int:item_id>", methods=["PUT"])
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


#################################################################
# SHARE A WISHLIST
#################################################################
@api.route("/wishlists/<int:wishlist_id>/share")
@api.param("wishlist_id", "The Wishlist identifier")
class ShareWishlistResource(Resource):
    """
    ShareWishlistResource class

    Allows generating a shareable link for a wishlist
    PUT /wishlists/{id}/share - Generate a shareable URL for the wishlist
    """

    @api.doc("share_wishlist")
    @api.response(200, "Share link generated")
    @api.response(404, "Wishlist not found")
    def put(self, wishlist_id):
        """
        Generate a shareable URL
        """
        app.logger.info("Request to generate share link for Wishlist [%s]", wishlist_id)
        wishlist = Wishlist.find(wishlist_id)
        if not wishlist:
            abort(
                status.HTTP_404_NOT_FOUND,
                f"Wishlist with id '{wishlist_id}' was not found.",
            )
        share_url = request.host_url + f"api/wishlists/{wishlist.id}"
        return {"share_url": share_url}, status.HTTP_200_OK


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
