# Backend

This directory contains the Python-based REST API for the Contract Intelligence Parser.

## Running the Application with Docker

To get the entire application stack (FastAPI backend, Celery worker, Redis, MongoDB, and the React frontend) up and running, you only need Docker and Docker Compose installed on your system.

1.  **Navigate to the Project Root:**
    Open your terminal and navigate to the root directory of this project where the `docker-compose.yml` file is located.

    ```bash
    cd /path/to/TechAssignment
    ```
    (Replace `/path/to/TechAssignment` with the actual path to your project directory.)

2.  **Build and Start the Services:**
    This command will build all necessary Docker images (backend, worker, frontend) and start all the services defined in `docker-compose.yml` (backend, worker, frontend, MongoDB, Redis).

    ```bash
    docker compose up --build
    ```

    *   The `--build` flag ensures that the images are built (or rebuilt if changes are detected) before starting the containers. This is especially important for the first-time setup.
    *   To run the services in the background (detached mode), add the `-d` flag:
        ```bash
        docker compose up --build -d
        ```

3.  **Access the Application:**
    Once all services are up and running, you can access the frontend application in your web browser at:
    [http://localhost:3000](http://localhost:3000)

4.  **Stop the Services:**
    To stop and remove the containers, networks, and volumes created by `docker compose up`:

    ```bash
    docker compose down
    ```

## Testing (within Docker)

If you need to run backend unit tests within the Docker environment, you can execute commands inside the running `backend` service container.

1.  **Find the backend service container ID/name:**
    ```bash
    docker ps
    ```
    Look for the container running the `backend` service.

2.  **Execute pytest:**
    ```bash
    docker exec <backend_container_id_or_name> pytest
    ```
    (Replace `<backend_container_id_or_name>` with the actual ID or name of your backend container.)