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
