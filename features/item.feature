Feature: Manage wishlist items
  Scenario: Create a wishlist item from the UI
    Given the Flask wishlist service is running
    And no wishlist exists for customer "CUST-ITEM" named "Tech Gadgets"
    And a wishlist exists for customer "CUST-ITEM" named "Tech Gadgets"
    When I visit the "Home Page"
    And I copy the created wishlist id into the item form
    And I set the "Product ID" to "5001"
    And I set the "Product Name" to "Noise Cancelling Headphones"
    And I set the "Price" to "199.99"
    And I press the "Create Item" button
    Then I should see the message "Wishlist item created successfully"

  Scenario: Retrieve a specific wishlist item from the UI
    Given the Flask wishlist service is running
    And no wishlist exists for customer "CUST-RETRIEVE" named "Electronics"
    And a wishlist exists for customer "CUST-RETRIEVE" named "Electronics"
    And an item exists in wishlist with product_id "2001" named "Laptop" with price "999.99"
    When I visit the "Home Page"
    And I copy the created wishlist id into the item form
    And I copy the created item id into the item id field
    And I press the "Retrieve Item" button
    Then I should see the message "Item retrieved successfully"
    And I should see "2001" in the "Product ID" field
    And I should see "Laptop" in the "Product Name" field
    And I should see "999.99" in the "Price" field

  Scenario: Update a wishlist entry
    Given the Flask wishlist service is running
    And no wishlist exists for customer "CUST-UPDATE-ITEM" named "Electronics"
    And a wishlist exists for customer "CUST-UPDATE-ITEM" named "Electronics"
    And an item exists in wishlist with product_id "3001" named "Camera" with price "499.99"
    When I visit the "Home Page"
    And I copy the created wishlist id into the item form
    And I copy the created item id into the item id field
    And I press the "Retrieve Item" button
    And I change "Product Name" to "GoPro"
    And I change "Price" to "599.99"
    And I press the "Update Item" button
    Then I should see the message "Item updated successfully"
    And I should see "GoPro" in the "Product Name" field
    And I should see "599.99" in the "Price" field

  Scenario: List all items in a wishlist without filters
    Given the Flask wishlist service is running
    And no wishlist exists for customer "CUST-LIST-ITEMS" named "Bag"
    And a wishlist exists for customer "CUST-LIST-ITEMS" named "Bag"
    And an item exists in wishlist with product_id "7001" named "Sling" with price "59.00"
    And an item exists in wishlist with product_id "7002" named "Backpack" with price "129.00"
    When I visit the "Home Page"
    And I copy the created wishlist id into the item form
    And I press the "Search Items" button
    Then I should see "Sling" in the results
    And I should see "Backpack" in the results

  Scenario: Query wishlist items by product name
    Given the Flask wishlist service is running
    And no wishlist exists for customer "CUST-ITEM-QUERY" named "Outdoor Gear"
    And a wishlist exists for customer "CUST-ITEM-QUERY" named "Outdoor Gear"
    And an item exists in wishlist with product_id "8101" named "Tent" with price "150.00"
    And an item exists in wishlist with product_id "8102" named "Lantern" with price "35.00"
    When I visit the "Home Page"
    And I copy the created wishlist id into the item form
    And I set the "Product Name" to "Tent"
    And I press the "Search Items" button
    Then I should see the message "Item search completed"
    And I should see "Tent" in the results
    And I should not see "Lantern" in the results

  Scenario: Query wishlist items by product id
    Given the Flask wishlist service is running
    And no wishlist exists for customer "CUST-ITEM-QUERY2" named "Gadgets"
    And a wishlist exists for customer "CUST-ITEM-QUERY2" named "Gadgets"
    And an item exists in wishlist with product_id "9101" named "Smartwatch" with price "220.00"
    And an item exists in wishlist with product_id "9102" named "Earbuds" with price "89.00"
    When I visit the "Home Page"
    And I copy the created wishlist id into the item form
    And I set the "Product ID" to "9101"
    And I press the "Search Items" button
    Then I should see the message "Item search completed"
    And I should see "Smartwatch" in the results
    And I should not see "Earbuds" in the results
