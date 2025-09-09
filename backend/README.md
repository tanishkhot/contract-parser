# Backend

This directory contains the Python-based REST API for the Contract Intelligence Parser.

## Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.10+
- Pip
- A running Redis instance. You can start one with Docker:
  ```bash
  docker run -d -p 6379:6379 redis
  ```

## Installation

1.  **Create and activate a virtual environment:**

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  **Install the dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

1.  **Start the FastAPI server:**

    In a terminal window, run:

    ```bash
    uvicorn main:app --reload --app-dir .
    ```

2.  **Start the Celery worker:**

    In a separate terminal window, run:

    ```bash
    celery -A celery_worker worker --loglevel=info
    ```

## Testing

To run the unit tests, run the following command in your terminal:

```bash
pytest
```
