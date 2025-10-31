Feature: Admin UI loads successfully
  Scenario: Load the admin UI page
    Given the Flask wishlist service is running
    When I visit the "Home Page"
    Then I should see "Wishlist Admin UI" in the title