# RESTful API Service for Wishlists

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Language-Python-blue.svg)](https://python.org/)
[![Build Status](https://github.com/CSCI-GA-2820-FA25-003/wishlists/actions/workflows/ci.yml/badge.svg)](https://github.com/CSCI-GA-2820-FA25-003/wishlists/actions)
[![codecov](https://codecov.io/gh/CSCI-GA-2820-FA25-003/wishlists/graph/badge.svg?token=8K1RZQONPO)](https://codecov.io/gh/CSCI-GA-2820-FA25-003/wishlists)



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

3. Deploying to Kubernetes

   This service can also be deployed locally to a Kubernetes cluster using the provided Makefile commands:

```bash
make cluster        # create a local k3d cluster
make build          # build the Docker image
make push           # push image to local registry
make deploy         # deploy all manifests under ./k8s
```

Service will run at http://localhost:8080/

## API Documents

| **Method** | **Endpoint**                               | **Purpose / Description**                                         |
| :--------- | :----------------------------------------- | :---------------------------------------------------------------- |
| **GET** | `/` | return index.html |
| **GET** | `/api` | Get service metadata |
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
| **PUT**    | `/wishlists/{wishlist_id}/clear` | Clear all items from a wishlist  |  
| **PUT**    | `/wishlists/{wishlist_id}/share` | Share a wishlist  | 

**Query Parameters**

	GET /wishlists
	  •customer_id (string): filter wishlists by customer
	  •name (string): requires customer_id; case-insensitive substring match on wishlist name
	  •If any unknown query parameter is present → 400 Bad Request
	GET /wishlists/{wishlist_id}/items
	  •product_id (int): exact match
	  •product_name (string): case-insensitive substring match
	  •If any unknown query parameter is present → 400 Bad Request

**Sample Commands**
  
1. Create a wishlist
```
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "User001", "name": "Holiday Gifts", "description": "Winter wishlist"}' \
  http://localhost:8080/wishlists
```

2. Get all wishlists
```
curl -X GET http://localhost:8080/wishlists
curl -X GET http://localhost:8080/wishlists?customer_id=12345
curl -X GET http://localhost:8080/wishlists?customer_id=12345&name=deal
```

3. Update a wishlist
```
curl -X PUT \
  -H "Content-Type: application/json" \
  -H "X-Customer-Id: User001" \
  -d '{"name": "Holiday Gifts Updated"}' \
  http://localhost:8080/wishlists/1
```

4. Delete a wishlist
```
curl -X DELETE http://localhost:8080/wishlists/1
```

5. Add an item to a wishlist
```
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"product_id": 123, "product_name": "Noise Cancelling Headphones", "price": 299.99}' \
  http://localhost:8080/wishlists/1/items
```

6. Get all items in a wishlist
```
curl -X GET http://localhost:8080/wishlists/1/items
curl -X GET http://localhost:8080/wishlists/1/items?product_id=123
curl -X GET http://localhost:8080/wishlists/1/items?product_name=Headphones
```

7. Update an item
```
curl -X PUT \
  -H "Content-Type: application/json" \
  -d '{
    "wishlist_id": 1,
    "customer_id": "User0001",
    "product_id": 123456,
    "product_name": "Headphones V2",
    "prices": 249.99,
    "wish_date": "2025-10-15T12:00:00-04:00"
  }' \
  http://localhost:8080/wishlists/1/items/2
```

8. Delete an item
```
curl -X DELETE http://localhost:8080/wishlists/1/items/2
```

9. Get a single item from a wishlist
```
curl -X GET http://localhost:8080/wishlists/1/items/2
```

10. Get a single wishlist
```
curl -X GET http://localhost:8080/wishlists/1
```

11. Clear a wishlist
```
curl -X PUT http://localhost:8080/wishlists/1/clear -i
```
12. Share a wishlist
```
curl -X PUT http://localhost:8080/wishlists/1/share -i
```


## Testing Instructions

Run the tests by:

```
pytest -q
```

Expected coverage: ≥ 95%

## Behavior-Driven Development (BDD) Tests

We implemented an admin UI and corresponding BDD tests using **Behave** and **Selenium** to verify end-to-end functionality (Create, Read, Update, Delete, List, Query, and Action).

### Running BDD Tests

```bash
flask run
```

Then, in another terminal:

```bash
behave
```

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
.
├── Dockerfile                - Docker build instructions
├── LICENSE                   - Apache 2.0 license
├── Makefile                  - Automation commands
├── Pipfile                   - Python dependencies for dev environment
├── Pipfile.lock              - Locked dependency versions
├── Procfile                  - Process definition for Honcho/Gunicorn
├── README.md                 - Project documentation
├── dot-env-example           - Example environment variable file
├── setup.cfg                 - Linting and formatting configuration
├── wsgi.py                   - WSGI entry point for Gunicorn
│
├── features/                 - BDD test scenarios and step definitions
│   ├── environment.py        - Behave environment setup
│   ├── item.feature          - BDD feature tests for wishlist items
│   ├── wishlist.feature      - BDD feature tests for wishlists
│   └── steps/
│       ├── item_steps.py     - Step definitions for item operations
│       ├── web_steps.py      - Browser UI interaction helpers
│       └── wishlist_steps.py - Step definitions for wishlist operations
│
├── k8s/                      - Kubernetes deployment manifests
│   ├── deployment.yaml       - App Deployment (Flask service)
│   ├── ingress.yaml          - Ingress route for external access
│   ├── service.yaml          - ClusterIP Service for Flask app
│   └── postgres/             - PostgreSQL StatefulSet & config files
│       ├── configmap.yaml
│       ├── pvc.yaml
│       ├── secret.yaml
│       ├── service.yaml
│       └── statefulset.yaml
│
├── service/                  - Flask application source code
│   ├── __init__.py
│   ├── config.py             - Application configuration
│   ├── routes.py             - API route definitions
│   ├── common/               - Shared utilities
│   │   ├── cli_commands.py   - CLI for DB initialization
│   │   ├── error_handlers.py - Error handling and HTTP codes
│   │   ├── log_handlers.py   - Logging setup
│   │   └── status.py         - HTTP status constants
│   ├── models/               - Data models and ORM logic
│   │   ├── persistent_base.py
│   │   ├── wishlist.py
│   │   └── item.py
│   └── static/               - Web UI files
│       ├── css/
│       ├── images/
│       ├── js/
│       └── index.html        - Admin UI for wishlists
│
└── tests/                    - Pytest unit and integration tests
    ├── factories.py          - Factory for generating test data
    ├── test_cli_commands.py  - CLI command tests
    ├── test_item.py          - Wishlist item model tests
    ├── test_routes.py        - API endpoint tests
    └── test_wishlist.py      - Wishlist model tests
```

## License

Copyright (c) 2016, 2025 [John Rofrano](https://www.linkedin.com/in/JohnRofrano/). All rights reserved.

Licensed under the Apache License. See [LICENSE](LICENSE)

This repository is part of the New York University (NYU) masters class: **CSCI-GA.2820-001 DevOps and Agile Methodologies** created and taught by [John Rofrano](https://cs.nyu.edu/~rofrano/), Adjunct Instructor, NYU Courant Institute, Graduate Division, Computer Science, and NYU Stern School of Business.
