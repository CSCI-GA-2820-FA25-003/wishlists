Feature: Admin UI loads successfully
  Scenario: Load the admin UI page
    Given the Flask wishlist service is running
    When I visit the "Home Page"
    Then I should see "Wishlist Admin UI" in the title

  Scenario: Create a wishlist from the UI
    Given the Flask wishlist service is running
    And no wishlist exists for customer "CUST-001" named "Spring Gifts"
    When I visit the "Home Page"
    And I set the "Customer ID" to "CUST-001"
    And I set the "Wishlist Name" to "Spring Gifts"
    And I set the "Description" to "Presents for spring"
    And I press the "Create Wishlist" button
    Then I should see the message "Wishlist created successfully"
    And I should see "Spring Gifts" in the "Wishlist Name" field

  Scenario: Read a wishlist and display contents
    Given the Flask wishlist service is running
    And no wishlist exists for customer "CUST-VIEW" named "Birthday Gifts"
    And a wishlist exists for customer "CUST-VIEW" named "Birthday Gifts"
    And an item exists in wishlist with product_id "1001" named "Watch" with price "199.99"
    And an item exists in wishlist with product_id "1002" named "Gift Card" with price "50.00"
    When I visit the "Home Page"
    And I copy the created wishlist id into the wishlist field
    And I press the "Retrieve Wishlist" button
    Then I should see the message "Wishlist retrieved successfully"
    And I should see "Birthday Gifts" in the "Wishlist Name" field
    And I should see "CUST-VIEW" in the "Customer ID" field
    And I should see "Watch" in the results
    And I should see "Gift Card" in the results

  Scenario: Update a wishlist name and description
    Given the Flask wishlist service is running
    And no wishlist exists for customer "CUST-UPDATE" named "Holiday Gifts"
    And no wishlist exists for customer "CUST-UPDATE" named "Travel Gifts"
    And a wishlist exists for customer "CUST-UPDATE" named "Holiday Gifts"
    When I visit the "Home Page"
    And I copy the created wishlist id into the wishlist field
    And I press the "Retrieve Wishlist" button
    And I change "Wishlist Name" to "Travel Gifts"
    And I change "Description" to "Gifts for traveling"
    And I press the "Update Wishlist" button
    Then I should see the message "Wishlist updated successfully"
    And I should see "Travel Gifts" in the "Wishlist Name" field
    And I should see "Gifts for traveling" in the "Description" field

  Scenario: List all wishlists without filters
    Given the Flask wishlist service is running
    And no wishlist exists for customer "CUST-LIST-A" named "Alpha"
    And no wishlist exists for customer "CUST-LIST-B" named "Beta"
    And a wishlist exists for customer "CUST-LIST-A" named "Alpha"
    And a wishlist exists for customer "CUST-LIST-B" named "Beta"
    When I visit the "Home Page"
    And I press the "Search Wishlists" button
    Then I should see "Alpha" in the results
    And I should see "Beta" in the results

  Scenario: Filter wishlists by partial name
    Given the Flask wishlist service is running
    And no wishlist exists for customer "CUST-FILTER-WL" named "Holiday Shopping"
    And a wishlist exists for customer "CUST-FILTER-WL" named "Holiday Shopping"
    When I visit the "Home Page"
    And I set the "Filter Wishlists" field to "Holiday"
    And I press the "Search Wishlists" filter button
    Then I should see "Holiday Shopping" in the wishlist results
    And I should see "Wishlist" in the page header above the wishlist results