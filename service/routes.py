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
from flask import jsonify, request, abort
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
    "WishlistCreate",
    {
        "name": fields.String(
            required=True,
            description="The name of the wishlist",
            example="My Birthday Wishlist",
        ),
        "customer_id": fields.String(
            required=True,
            description="The unique identifier of the customer who owns this wishlist",
            example="CUST001",
        ),
        "description": fields.String(
            required=False,
            description="An optional description of the wishlist",
            example="Things I want for my birthday",
        ),
    },
)

wishlist_model = api.model(
    "Wishlist",
    {
        "id": fields.Integer(
            readOnly=True,
            description="The unique identifier of the wishlist",
            example=1,
        ),
        "name": fields.String(
            required=True,
            description="The name of the wishlist",
            example="My Birthday Wishlist",
        ),
        "customer_id": fields.String(
            required=True,
            description="The unique identifier of the customer who owns this wishlist",
            example="CUST001",
        ),
        "description": fields.String(
            required=False,
            description="An optional description of the wishlist",
            example="Things I want for my birthday",
        ),
        "created_at": fields.DateTime(
            readOnly=True,
            description="Timestamp when the wishlist was created",
        ),
        "updated_at": fields.DateTime(
            readOnly=True,
            description="Timestamp when the wishlist was last updated",
        ),
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

# Define the WishlistItem models
create_item_model = api.model(
    "WishlistItem",
    {
        "product_id": fields.Integer(
            required=True,
            description="The unique identifier of the product",
            example=12345,
        ),
        "product_name": fields.String(
            required=True,
            description="The name of the product",
            example="Wireless Headphones",
        ),
        "prices": fields.Float(
            required=True,
            description="The price of the product at the time it was added",
            example=79.99,
        ),
    },
)

item_model = api.inherit(
    "WishlistItemModel",
    create_item_model,
    {
        "id": fields.Integer(
            readOnly=True,
            description="The unique identifier of the wishlist item",
            example=1,
        ),
        "wishlist_id": fields.Integer(
            readOnly=True, description="The ID of the parent wishlist", example=1
        ),
        "customer_id": fields.String(
            readOnly=True,
            description="The ID of the customer who owns the wishlist",
            example="CUST001",
        ),
        "wish_date": fields.DateTime(
            readOnly=True,
            description="The date and time when the item was added to the wishlist",
            example="2024-12-05T10:30:00Z",
        ),
    },
)

# Add items field to wishlist_model after item_model is defined
wishlist_model["items"] = fields.List(
    fields.Nested(item_model),
    description="List of items in the wishlist",
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
                "list_all_wishlists": f"{base}/api/wishlists",
                "create_wishlist": f"{base}/api/wishlists",
                "get_wishlist": f"{base}/api/wishlists/{{wishlist_id}}",
                "update_wishlist": f"{base}/api/wishlists/{{wishlist_id}}",
                "delete_wishlist": f"{base}/api/wishlists/{{wishlist_id}}",
                # ----------- Wishlist Item endpoints -----------
                "list_wishlist_items": f"{base}/api/wishlists/{{wishlist_id}}/items",
                "create_wishlist_item": f"{base}/api/wishlists/{{wishlist_id}}/items",
                "get_wishlist_item": f"{base}/api/wishlists/{{wishlist_id}}/items/{{item_id}}",
                "update_wishlist_item": f"{base}/api/wishlists/{{wishlist_id}}/items/{{item_id}}",
                "delete_wishlist_item": f"{base}/api/wishlists/{{wishlist_id}}/items/{{item_id}}",
                # ----------- Action endpoints -----------
                "clear_wishlist": f"{base}/api/wishlists/{{wishlist_id}}/clear",
                "share_wishlist": f"{base}/api/wishlists/{{wishlist_id}}/share",
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
    @api.doc(
        params={
            "X-Customer-Id": {
                "in": "header",
                "description": "Customer ID (must match wishlist owner)",
                "required": True,
                "type": "string",
            }
        }
    )
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
        allowed_params = {"name", "customer_id"}
        request_params = set(request.args.keys())
        unknown_params = request_params - allowed_params
        if unknown_params:
            abort(
                status.HTTP_400_BAD_REQUEST,
                f"Unsupported query parameter(s): {', '.join(sorted(unknown_params))}",
            )
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
        # elif name:
        #     app.logger.info("Filtering by name: %s", name)
        #     all_lists = Wishlist.all()
        #     wishlists = [wl for wl in all_lists if name.lower() in wl.name.lower()]
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
        data = api.payload
        wishlist.customer_id = data["customer_id"]
        wishlist.name = data["name"]
        wishlist.description = data.get("description")
        wishlist.create()
        app.logger.info("Wishlist with id [%s] created.", wishlist.id)
        location_url = api.url_for(
            WishlistResource, wishlist_id=wishlist.id, _external=True
        )

        return wishlist.serialize(), status.HTTP_201_CREATED, {"Location": location_url}


######################################################################
#  PATH: /wishlists/{wishlist_id}/items
######################################################################
@api.route("/wishlists/<int:wishlist_id>/items")
@api.param("wishlist_id", "The Wishlist identifier")
class WishlistItemCollection(Resource):
    """Handles all interactions with Wishlist Items"""

    # ------------------------------------------------------------------
    # LIST ITEMS
    # ------------------------------------------------------------------
    @api.doc("list_wishlist_items")
    @api.response(404, "Wishlist not found")
    @api.response(400, "Bad request - invalid query parameters")
    @api.marshal_list_with(item_model)
    def get(self, wishlist_id):
        """
        List all Items in a Wishlist

        This endpoint will return all items in the specified wishlist.
        Supports optional filtering by product_id and product_name.
        """
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

        # Optional filtering by product_name (case-insensitive substring)
        if "product_name" in params and params["product_name"].strip():
            needle = params["product_name"].strip().lower()
            items = [it for it in items if needle in (it.product_name or "").lower()]

        results = [item.serialize() for item in items]
        return results, status.HTTP_200_OK

    # ------------------------------------------------------------------
    # ADD AN ITEM
    # ------------------------------------------------------------------
    @api.doc("create_wishlist_item")
    @api.response(400, "The posted data was not valid")
    @api.response(404, "Wishlist not found")
    @api.response(409, "Item already exists in wishlist")
    @api.expect(create_item_model)
    @api.marshal_with(item_model, code=201)
    def post(self, wishlist_id):
        """
        Add an Item to a Wishlist

        This endpoint will add a new item to the specified wishlist.
        Duplicate items (same product_id) are prevented.
        """
        app.logger.info("Request to add Item to Wishlist %s", wishlist_id)

        # Ensure wishlist exists
        wishlist = Wishlist.find(wishlist_id)
        if not wishlist:
            abort(
                status.HTTP_404_NOT_FOUND,
                f"Wishlist with id '{wishlist_id}' was not found.",
            )

        # Get payload from api.payload
        payload = api.payload

        # Validate required fields are present
        if not payload:
            abort(status.HTTP_400_BAD_REQUEST, "Request body is required")

        # product_id validation
        product_id = payload.get("product_id")
        if not isinstance(product_id, int):
            abort(status.HTTP_400_BAD_REQUEST, "product_id must be an integer")
        if product_id <= 0:
            abort(status.HTTP_400_BAD_REQUEST, "Invalid product_id: must be positive")

        # product_name validation
        product_name = payload.get("product_name")
        if not isinstance(product_name, str) or not product_name.strip():
            abort(
                status.HTTP_400_BAD_REQUEST, "product_name must be a non-empty string"
            )

        # price validation
        price = payload.get("prices")
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
        item = Item()
        item.wishlist_id = wishlist.id
        item.customer_id = wishlist.customer_id
        item.product_id = product_id
        item.product_name = product_name
        item.prices = price_val
        item.create()

        # Refetch to ensure server defaults (wish_date) are populated
        item = Item.find(item.id)

        location_url = api.url_for(
            WishlistItemResource,
            wishlist_id=wishlist.id,
            item_id=item.id,
            _external=True,
        )
        app.logger.info("Item %s added to Wishlist %s", item.id, wishlist.id)

        return item.serialize(), status.HTTP_201_CREATED, {"Location": location_url}


######################################################################
#  PATH: /wishlists/{wishlist_id}/items/{item_id}
######################################################################
@api.route("/wishlists/<int:wishlist_id>/items/<int:item_id>")
@api.param("wishlist_id", "The Wishlist identifier")
@api.param("item_id", "The Item identifier")
class WishlistItemResource(Resource):
    """
    WishlistItemResource class

    Allows manipulation of a single wishlist item
    GET /wishlists/{id}/items/{item_id} - Returns an Item
    PUT /wishlists/{id}/items/{item_id} - Updates an Item
    DELETE /wishlists/{id}/items/{item_id} - Deletes an Item
    """

    # ------------------------------------------------------------------
    # GET AN ITEM
    # ------------------------------------------------------------------
    @api.doc("get_wishlist_item")
    @api.response(404, "Item not found")
    @api.marshal_with(item_model)
    def get(self, wishlist_id, item_id):
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
        return item.serialize(), status.HTTP_200_OK

    # ------------------------------------------------------------------
    # UPDATE AN ITEM
    # ------------------------------------------------------------------
    @api.doc("update_wishlist_item")
    @api.response(404, "Item not found")
    @api.response(400, "The posted data was not valid")
    @api.expect(item_model)
    @api.marshal_with(item_model)
    def put(self, wishlist_id, item_id):
        """
        Update an Item in a Wishlist

        This endpoint will update an item in the specified wishlist
        """
        app.logger.info(
            "Request to update Item %s in Wishlist %s", item_id, wishlist_id
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

        # Update the item with the request data
        item.deserialize(api.payload)
        item.update()

        app.logger.info("Item with id [%s] updated.", item.id)
        return item.serialize(), status.HTTP_200_OK

    # ------------------------------------------------------------------
    # DELETE AN ITEM
    # ------------------------------------------------------------------
    @api.doc("delete_wishlist_item")
    @api.response(204, "Item deleted")
    def delete(self, wishlist_id, item_id):
        """
        Delete an Item from a Wishlist

        This endpoint will delete an item from the specified wishlist.
        Returns 204 even if the item doesn't exist (idempotent).
        """
        app.logger.info(
            "Request to delete Item [%s] from Wishlist [%s]", item_id, wishlist_id
        )

        item = Item.find(item_id)

        if item and item.wishlist_id == wishlist_id:
            item.delete()
            app.logger.info(
                "Item [%s] deleted from Wishlist [%s]", item_id, wishlist_id
            )
        else:
            app.logger.info(
                "Item [%s] not present in Wishlist [%s]; returning 204 (idempotent)",
                item_id,
                wishlist_id,
            )

        return "", status.HTTP_204_NO_CONTENT


#################################################################
# CLEAR A WISHLIST item
#################################################################
@api.route("/wishlists/<int:wishlist_id>/clear")
@api.param("wishlist_id", "The Wishlist identifier")
class ClearWishlistResource(Resource):
    """Clear all items from a wishlist"""

    @api.doc("clear_wishlist")
    @api.response(204, "Wishlist cleared")
    @api.response(404, "Wishlist not found")
    def put(self, wishlist_id):
        """Clear all items in the specified wishlist."""
        app.logger.info("Request to clear all items in Wishlist [%s]", wishlist_id)

        wishlist = Wishlist.find(wishlist_id)
        if not wishlist:
            abort(
                status.HTTP_404_NOT_FOUND,
                f"Wishlist with id '{wishlist_id}' was not found.",
            )

        wishlist.clear_items()

        return "", status.HTTP_204_NO_CONTENT


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
