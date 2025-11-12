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

  Scenario: Query wishlists by customer filter
    Given the Flask wishlist service is running
    And no wishlist exists for customer "CUST-QUERY-1" named "Preferred Gifts"
    And no wishlist exists for customer "CUST-QUERY-2" named "Other Gifts"
    And a wishlist exists for customer "CUST-QUERY-1" named "Preferred Gifts"
    And a wishlist exists for customer "CUST-QUERY-2" named "Other Gifts"
    When I visit the "Home Page"
    And I set the "Customer ID" to "CUST-QUERY-1"
    And I press the "Search Wishlists" button
    Then I should see the message "Wishlist search completed"
    And I should see "Preferred Gifts" in the results
    And I should not see "Other Gifts" in the results

  Scenario: Query wishlists by partial name filter
    Given the Flask wishlist service is running
    And no wishlist exists for customer "CUST-QUERY-NAME" named "Camping Gear"
    And no wishlist exists for customer "CUST-QUERY-NAME" named "Office Gear"
    And a wishlist exists for customer "CUST-QUERY-NAME" named "Camping Gear"
    And a wishlist exists for customer "CUST-QUERY-NAME" named "Office Gear"
    When I visit the "Home Page"
    And I set the "Customer ID" to "CUST-QUERY-NAME"
    And I set the "Wishlist Name" to "Camp"
    And I press the "Search Wishlists" button
    Then I should see the message "Wishlist search completed"
    And I should see "Camping Gear" in the results
    And I should not see "Office Gear" in the results

  Scenario: Delete a wishlist
    Given the Flask wishlist service is running
    And no wishlist exists for customer "99999" named "Temp List"
    And a wishlist exists for customer "99999" named "Temp List"
    When I copy the created wishlist id into the wishlist form
    And I click the "Delete Wishlist" button
    Then "Temp List" should not appear in the list

  Scenario: Clear wishlist and share wishlist
    Given the Flask wishlist service is running
    And a wishlist named "Holiday Gifts"
    When I click "Share" for that wishlist
    And I click "Clear" for that wishlist
    Then the wishlist link should show
    And the wishlist should show as empty