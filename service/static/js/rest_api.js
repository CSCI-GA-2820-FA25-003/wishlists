$(function () {
    const $flash = $("#flash_message");

    const $wishlistId = $("#wishlist_id");
    const $wishlistCustomerId = $("#wishlist_customer_id");
    const $wishlistName = $("#wishlist_wishlist_name");
    const $wishlistDescription = $("#wishlist_description");

    const $itemWishlistId = $("#item_wishlist_id");
    const $itemId = $("#item_id");
    const $itemProductId = $("#item_product_id");
    const $itemProductName = $("#item_product_name");
    const $itemPrice = $("#item_price");

    function handleFail(res, fallback) {
        const message = res.responseJSON?.message || res.responseText || fallback || "Server error";
        flashMessage(message);
    }

    function flashMessage(message) {
        $flash.empty();
        if (message) {
            $flash.append(message);
        }
    }

    // /* ===== Extended Wishlist & Item Features (Optional) START =====
    const $searchResults = $("#search_results");
    const $itemResults = $("#item_results");

    function updateWishlistForm(data) {
        $wishlistId.val(data.id ?? "");
        $wishlistCustomerId.val(data.customer_id ?? "");
        $wishlistName.val(data.name ?? "");
        $wishlistDescription.val(data.description ?? "");
    }

    function clearWishlistForm() {
        $wishlistId.val("");
        $wishlistCustomerId.val("");
        $wishlistName.val("");
        $wishlistDescription.val("");
    }

    function updateItemForm(data) {
        $itemWishlistId.val(data.wishlist_id ?? $itemWishlistId.val());
        $itemId.val(data.id ?? "");
        $itemProductId.val(data.product_id ?? "");
        $itemProductName.val(data.product_name ?? "");
        const price = data.prices ?? data.price;
        $itemPrice.val(price !== undefined && price !== null ? price : "");
    }

    function clearItemForm() {
        $itemWishlistId.val("");
        $itemId.val("");
        $itemProductId.val("");
        $itemProductName.val("");
        $itemPrice.val("");
    }

    function renderWishlistTable(wishlists) {
        $("#search_results").find("table").remove();
        if (!wishlists || wishlists.length === 0) {
            $searchResults.append("<p>No wishlists found.</p>");
            return;
        }

        let table = '<table class="table table-striped" cellpadding="10">';
        table += "<thead><tr>";
        table += '<th class="col-md-2">ID</th>';
        table += '<th class="col-md-3">Customer ID</th>';
        table += '<th class="col-md-3">Name</th>';
        table += '<th class="col-md-4">Description</th>';
        table += "</tr></thead><tbody>";

        wishlists.forEach((wishlist, index) => {
            table += `<tr id="wishlist_row_${index}"><td>${wishlist.id ?? ""}</td><td>${wishlist.customer_id ?? ""}</td><td>${wishlist.name ?? ""}</td><td>${wishlist.description ?? ""}</td></tr>`;
        });

        table += "</tbody></table>";
        $searchResults.append(table);
        updateWishlistForm(wishlists[0]);
    }

    function renderItemTable(items) {
        $("#item_results").find("table").remove();
        if (!items || items.length === 0) {
            $itemResults.append("<p>No items found.</p>");
            return;
        }

        let table = '<table class="table table-striped" cellpadding="10">';
        table += "<thead><tr>";
        table += '<th class="col-md-2">Item ID</th>';
        table += '<th class="col-md-2">Product ID</th>';
        table += '<th class="col-md-4">Product Name</th>';
        table += '<th class="col-md-2">Price</th>';
        table += "</tr></thead><tbody>";

        items.forEach((item, index) => {
            const price = (item.price ?? item.prices) ?? "";
            table += `<tr id="item_row_${index}">
            <td>${item.id ?? ""}</td>
            <td>${item.product_id ?? ""}</td>
            <td>${item.product_name ?? ""}</td>
            <td>${price}</td>
            </tr>`;
        });

        table += "</tbody></table>";
        $itemResults.append(table);
        updateItemForm(items[0]);
    }

    $("#update_wishlist-btn").click(function () {
        const wishlistId = $wishlistId.val();
        // console.log("[DEBUG] Update clicked, wishlist ID:", wishlistId);
        // console.log("[DEBUG] Customer ID:", $wishlistCustomerId.val());
        // console.log("[DEBUG] Name:", $wishlistName.val());
        // console.log("[DEBUG] Description:", $wishlistDescription.val());
        
        if (!wishlistId) {
            flashMessage("Wishlist ID is required for update");
            return;
        }
        const data = {
            name: $wishlistName.val(),
            description: $wishlistDescription.val() || null,
        };
        flashMessage("");
        
        // console.log("[DEBUG] Sending PUT request...");
        
        $.ajax({
            type: "PUT",
            url: `/wishlists/${wishlistId}`,
            contentType: "application/json",
            headers: {
                "X-Customer-Id": $wishlistCustomerId.val(),
            },
            data: JSON.stringify(data),
        })
            .done(function (res) {
                // console.log("[DEBUG] Update succeeded:", res);
                updateWishlistForm(res);
                flashMessage("Wishlist updated successfully");
            })
            .fail(function (err) {
                // console.log("[DEBUG] Update failed:", err);
                handleFail(err);
            });
    });

    $("#retrieve_wishlist-btn").click(function () {
        const wishlistId = $wishlistId.val();
        // console.log("[DEBUG] Retrieve clicked, wishlist ID:", wishlistId);
        
        if (!wishlistId) {
            flashMessage("Please enter a Wishlist ID to retrieve");
            return;
        }
    
        flashMessage("");
    
        $.ajax({
            type: "GET",
            url: `/wishlists/${wishlistId}`,
            contentType: "application/json",
        })
            .done(function (res) {
                // console.log("[DEBUG] Wishlist API response:", res);
                // console.log("[DEBUG] Name from API:", res.name);
                
                updateWishlistForm(res);
                
                // console.log("[DEBUG] After updateWishlistForm:");
                // console.log("[DEBUG]   - wishlist_id field:", $wishlistId.val());
                // console.log("[DEBUG]   - customer_id field:", $wishlistCustomerId.val());
                // console.log("[DEBUG]   - name field:", $wishlistName.val());
                // console.log("[DEBUG]   - description field:", $wishlistDescription.val());
                
                // Also fetch the items for this wishlist
                $.ajax({
                    type: "GET",
                    url: `/wishlists/${wishlistId}/items`,
                    contentType: "application/json",
                })
                    .done(function (items) {
                        // console.log("[DEBUG] Items API response:", items);
                        renderItemTable(items);
                        flashMessage("Wishlist retrieved successfully");
                    })
                    .fail(function (err) {
                        // console.log("[DEBUG] Items fetch failed:", err);
                        flashMessage("Wishlist retrieved successfully");
                    });
            })
            .fail(function (res) {
                // console.log("[DEBUG] Wishlist fetch failed:", res);
                clearWishlistForm();
                handleFail(res);
            });
    });

    $("#delete_wishlist-btn").click(function () {
        const wishlistId = $wishlistId.val();
        if (!wishlistId) {
            flashMessage("Please enter a Wishlist ID to delete");
            return;
        }

        flashMessage("");

        $.ajax({
            type: "DELETE",
            url: `/wishlists/${wishlistId}`,
            contentType: "application/json",
        })
            .done(function () {
                clearWishlistForm();
                flashMessage("Wishlist deleted successfully");
            })
            .fail(handleFail);
    });

    $("#clear_form_fields-btn").click(function () {
        $wishlistId.val("");
        flashMessage("");
        clearWishlistForm();
    });
    
    $("#search_wishlists-btn").click(function () {
        const customerId = $wishlistCustomerId.val();
        const name = $wishlistName.val();
        const params = [];

        if (customerId) {
            params.push(`customer_id=${encodeURIComponent(customerId)}`);
        }
        if (name) {
            params.push(`name_contains=${encodeURIComponent(name)}`);
        }

        const queryString = params.length > 0 ? `?${params.join("&")}` : "";

        flashMessage("");

        $.ajax({
            type: "GET",
            url: `/wishlists${queryString}`,
            contentType: "application/json",
        })
            .done(function (res) {
                renderWishlistTable(res);
                flashMessage("Wishlist search completed");
            })
            .fail(handleFail);
    });

    $("#clear_wishlist-btn").click(function () {
        const wishlistId = $wishlistId.val();
        if (!wishlistId) {
            flashMessage("Wishlist ID is required to clear a wishlist");
            return;
        }

        flashMessage("");

        $.ajax({
            type: "PUT",
            url: `/wishlists/${wishlistId}/clear`,
            contentType: "application/json",
        })
            .done(function () {
                flashMessage("Wishlist cleared successfully");
            })
            .fail(handleFail);
    });

    $("#share_wishlist-btn").click(function () {
        const wishlistId = $wishlistId.val();
        if (!wishlistId) {
            flashMessage("Wishlist ID is required to share a wishlist");
            return;
        }

        flashMessage("");

        $.ajax({
            type: "PUT",
            url: `/wishlists/${wishlistId}/share`,
            contentType: "application/json",
        })
            .done(function (res) {
                const shareUrl = res.share_url || "";
                if (shareUrl) {
                    const link = `<a href="${shareUrl}" target="_blank" rel="noopener noreferrer">${shareUrl}</a>`;
                    flashMessage(`Share URL: ${link}`);
                } else {
                    flashMessage("Share link generated successfully");
                }
            })
            .fail(handleFail);
    });

    $("#update_item-btn").click(function () {
        const wishlistId = $itemWishlistId.val();
        const itemId = $itemId.val();
        if (!wishlistId || !itemId) {
            flashMessage("Wishlist ID and Item ID are required for update");
            return;
        }

        const productIdVal = $itemProductId.val();
        const priceVal = $itemPrice.val();
        const data = {
            product_id: productIdVal ? Number(productIdVal) : null,
            product_name: $itemProductName.val(),
            price: priceVal ? Number(priceVal) : null,
        };

        flashMessage("");

        $.ajax({
            type: "PUT",
            url: `/wishlists/${wishlistId}/items/${itemId}`,
            contentType: "application/json",
            data: JSON.stringify(data),
        })
            .done(function (res) {
                updateItemForm(res);
                flashMessage("Item updated successfully");
            })
            .fail(handleFail);
    });

    $("#retrieve_item-btn").click(function () {
        const wishlistId = $itemWishlistId.val();
        const itemId = $itemId.val();
        if (!wishlistId || !itemId) {
            flashMessage("Wishlist ID and Item ID are required to retrieve an item");
            return;
        }

        flashMessage("");

        $.ajax({
            type: "GET",
            url: `/wishlists/${wishlistId}/items/${itemId}`,
            contentType: "application/json",
        })
            .done(function (res) {
                updateItemForm(res);
                flashMessage("Item retrieved successfully");
            })
            .fail(function (res) {
                clearItemForm();
                handleFail(res);
            });
    });

    $("#delete_item-btn").click(function () {
        const wishlistId = $itemWishlistId.val();
        const itemId = $itemId.val();
        if (!wishlistId || !itemId) {
            flashMessage("Wishlist ID and Item ID are required to delete an item");
            return;
        }

        flashMessage("");

        $.ajax({
            type: "DELETE",
            url: `/wishlists/${wishlistId}/items/${itemId}`,
            contentType: "application/json",
        })
            .done(function () {
                clearItemForm();
                flashMessage("Item deleted successfully");
            })
            .fail(handleFail);
    });

    $("#clear_item-btn").click(function () {
        clearItemForm();
        flashMessage("");
    });

    $("#search_items-btn").click(function () {
        const wishlistId = $itemWishlistId.val();
        if (!wishlistId) {
            flashMessage("Wishlist ID is required to search items");
            return;
        }

        const productId = $itemProductId.val();
        const productName = $itemProductName.val();
        const params = [];

        if (productId) {
            params.push(`product_id=${encodeURIComponent(productId)}`);
        }
        if (productName) {
            params.push(`product_name_contains=${encodeURIComponent(productName)}`);
        }
        const queryString = params.length > 0 ? `?${params.join("&")}` : "";

        flashMessage("");

        $.ajax({
            type: "GET",
            url: `/wishlists/${wishlistId}/items${queryString}`,
            contentType: "application/json",
        })
            .done(function (res) {
                renderItemTable(res);
                if (res.length > 0) {
                    $itemWishlistId.val(res[0].wishlist_id ?? wishlistId);
                }
                flashMessage("Item search completed");
            })
            .fail(handleFail);
    });
    // ===== Extended Wishlist & Item Features (Optional) END ===== */

    $("#create_wishlist-btn").click(function () {
        const payload = {
            customer_id: $wishlistCustomerId.val(),
            name: $wishlistName.val(),
            description: $wishlistDescription.val() || null,
        };

        if (!payload.customer_id || !payload.name) {
            flashMessage("customer_id and name are required to create a wishlist");
            return;
        }

        flashMessage("");

        $.ajax({
            type: "POST",
            url: "/wishlists",
            contentType: "application/json",
            data: JSON.stringify(payload),
        })
            .done(function (res) {
                if (typeof updateWishlistForm === "function") {
                    updateWishlistForm(res);
                } else {
                    $wishlistId.val(res.id ?? "");
                }
                flashMessage("Wishlist created successfully");
            })
            .fail(function (res) {
                handleFail(res, "Failed to create wishlist");
            });
    });

    $("#create_item-btn").click(function () {
        const wishlistId = $itemWishlistId.val();
        if (!wishlistId) {
            flashMessage("wishlist_id is required to create an item");
            return;
        }

        const productIdVal = $itemProductId.val();
        const priceVal = $itemPrice.val();
        const payload = {
            product_id: productIdVal ? Number(productIdVal) : null,
            product_name: $itemProductName.val(),
            price: priceVal ? Number(priceVal) : null,
        };

        if (!payload.product_id || !payload.product_name) {
            flashMessage("product_id and product_name are required to create an item");
            return;
        }

        if (Number.isNaN(payload.product_id) || payload.product_id <= 0) {
            flashMessage("product_id must be a positive number");
            return;
        }

        if (payload.price === null || Number.isNaN(payload.price) || payload.price < 0) {
            flashMessage("price must be a non-negative number");
            return;
        }

        flashMessage("");

        $.ajax({
            type: "POST",
            url: `/wishlists/${wishlistId}/items`,
            contentType: "application/json",
            data: JSON.stringify(payload),
        })
            .done(function (res) {
                if (typeof updateItemForm === "function") {
                    updateItemForm(res);
                }
                flashMessage("Wishlist item created successfully");
            })
            .fail(function (res) {
                handleFail(res, "Failed to create wishlist item");
            });
    });
});
