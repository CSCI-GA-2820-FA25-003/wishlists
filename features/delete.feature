Feature: Delete wishlist and item via admin UI
  Scenario: Successfully delete wishlist and item
    Given the Flask wishlist service is running
    And no wishlist exists for customer "99999" named "Temp List"
    And a wishlist exists for customer "99999" named "Temp List"
    When I copy the created wishlist id into the item form
    And an item exists in wishlist with product_id "555" named "Old Phone" with price "199.99"
    When I copy the created item id into the item id field
    And I copy the created wishlist id into the wishlist field
    When I click the "Delete Item" button
    And I click the "Delete Wishlist" button
    Then neither "Temp List" nor "Old Phone" should appear in the list
