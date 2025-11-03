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
