# RESTful API Service for Wishlists

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Language-Python-blue.svg)](https://python.org/)

This is a documentation for API usage on Wishlists.

## Service Overview

This is a Flask-based RESTful API for managing customer **wishlists** and their items. It supports basic CRUD operations for wishlists and nested CRUD operations for items.

## Prerequisites

It is recommended to run this project in a Dev Container for consistent dependencies.

Make sure you have installed:

* Docker

* VS Code

* Dev Containers extension

## Getting Started

Follow these steps to clone the repository, start the development environment, and run the API.

1. Clone the Repository
```
git clone https://github.com/CSCI-GA-2820-FA25-003/wishlists.git
cd wishlists
```

2. Open in VS Code and Reopen in Container
When ready, start the service:

```bash
honcho start
```

Service will run at http://localhost:8080/

## API Documents

| **Method** | **Endpoint**                               | **Purpose / Description**                                         |
| :--------- | :----------------------------------------- | :---------------------------------------------------------------- |
| **GET** | / | Get service metadata (root endpoint) |
| **GET**    | `/wishlists`                               | Get a list of all wishlists of a customer                         |
| **GET**    | `/wishlists/{wishlist_id}`                 | Get details of a specific wishlist                                |
| **POST**   | `/wishlists`                               | Create a new wishlist for a customer                              |
| **PUT**    | `/wishlists/{wishlist_id}`                 | Update the attributes (name, description) of an existing wishlist |
| **DELETE** | `/wishlists/{wishlist_id}`                 | Delete a wishlist                                                 |
| **GET**    | `/wishlists/{wishlist_id}/items`           | Get all items of a specific wishlist                              |
| **GET**    | `/wishlists/{wishlist_id}/items/{item_id}` | Get one specific item from a wishlist                             |
| **POST**   | `/wishlists/{wishlist_id}/items`           | Add a new item to a wishlist                                      |
| **PUT**    | `/wishlists/{wishlist_id}/items/{item_id}` | Update details of an existing item                                |
| **DELETE** | `/wishlists/{wishlist_id}/items/{item_id}` | Remove an item from a wishlist                                    |


**Sample Commands**
  
1. Create a wishlist
```
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "User001", "name": "Holiday Gifts", "description": "Winter wishlist"}' \
  http://localhost:8080/wishlists
```

1. Get all wishlists
```
curl -X GET http://localhost:8080/wishlists
```

1. Update a wishlist
```
curl -X PUT \
  -H "Content-Type: application/json" \
  -H "X-Customer-Id: User001" \
  -d '{"name": "Holiday Gifts Updated"}' \
  http://localhost:8080/wishlists/1
```

1. Delete a wishlist
```
curl -X DELETE http://localhost:8080/wishlists/1
```

1. Add an item to a wishlist
```
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"product_id": 123, "product_name": "Noise Cancelling Headphones", "price": 299.99}' \
  http://localhost:8080/wishlists/1/items
```

1. Get all items in a wishlist
```
curl -X GET http://localhost:8080/wishlists/1/items
```

1. Update an item
```
curl -X PUT \
  -H "Content-Type: application/json" \
  -d '{"product_name": "Headphones V2", "price": 249.99}' \
  http://localhost:8080/wishlists/1/items/2
```

1. Delete an item
```
curl -X DELETE http://localhost:8080/wishlists/1/items/2
```

1. Get a single item from a wishlist
```
curl -X GET http://localhost:8080/wishlists/1/items/2
```

1.  Get a single wishlist
```
curl -X GET http://localhost:8080/wishlists/1
```

## Testing Instructions

Run the tests by:

```
pytest -q
```

Expected coverage: ≥ 95%

## Development Workflow

1. Create a feature branch

```
git checkout -b feature/<task-name>
```

2. Commit and push changes

```
git add .
git commit -m "feat: <short description>"
git push origin feature/<task-name>
```

3. Open a Pull Request on GitHub

* Link the related issue (Issue #<number>)

* Wait for code review before merging and closing


## Troubleshooting 

| Problem                      | Likely Cause                | Solution                                  |
| ---------------------------- | --------------------------- | ----------------------------------------- |
| `415 Unsupported Type` | Missing JSON header         | Add `-H "Content-Type: application/json"` |
| `403 Forbidden`              | Wrong customer ID header    | Use correct `X-Customer-Id`               |
| `404 Not Found`              | Invalid wishlist or item ID | Check existing IDs via list endpoints     |


## Contents

The project contains the following:

```text
.gitignore          - this will ignore vagrant and other metadata files
.flaskenv           - Environment variables to configure Flask
.gitattributes      - File to gix Windows CRLF issues
.devcontainers/     - Folder with support for VSCode Remote Containers
dot-env-example     - copy to .env to use environment variables
pyproject.toml      - Poetry list of Python libraries required by your code


service/                    - main service package
├── __init__.py             - package initializer
├── config.py               - configuration parameters
├── routes.py               - Flask route definitions for all endpoints
├── models/                 - package containing data models
│   ├── __init__.py         - model package initializer
│   ├── persistent_base.py  - base model with shared DB logic
│   ├── wishlist.py         - Wishlist model class
│   └── item.py             - Item model class
│
└── common/                 - common utilities package
    ├── cli_commands.py     - Flask CLI command to recreate all tables
    ├── error_handlers.py   - HTTP error handling code
    ├── log_handlers.py     - logging setup code
    └── status.py           - HTTP status constants

tests/                     - test cases package
├── __init__.py            - package initializer
├── factories.py           - Factory for testing with fake objects
├── test_cli_commands.py   - test suite for the CLI
├── test_models.py         - test suite for business models
├── test_routes.py         - test suite for service routes
└── test_wishlist.py       - test suite for wishlist features
```

## License

Copyright (c) 2016, 2025 [John Rofrano](https://www.linkedin.com/in/JohnRofrano/). All rights reserved.

Licensed under the Apache License. See [LICENSE](LICENSE)

This repository is part of the New York University (NYU) masters class: **CSCI-GA.2820-001 DevOps and Agile Methodologies** created and taught by [John Rofrano](https://cs.nyu.edu/~rofrano/), Adjunct Instructor, NYU Courant Institute, Graduate Division, Computer Science, and NYU Stern School of Business.
