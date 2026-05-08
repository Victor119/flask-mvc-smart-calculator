Implemented a microservice that exposes an API to solve different mathematical operations:
- the pow function  (extended into a general-purpose calculator function)
- the n-th Fibonacci number
- the factorial of the number
 
The service uses a database to persist all API requests and is exposed as a RESTful API (not SOAP). It has been designed as a production-ready service.
 
Additionally, I have implemented containerization, monitoring, caching for performance optimization, authorization, logging.
 
All implementation and design follow the constraints below:
- using a micro-framework (Flask was used for simplicity)
- adherence to microservices best practices (MVC/MVCS architecture)
- RESTful API design
- extensible design to support future features
- as the database layer, use any SQL or NoSQL solution (SQLite used for simplicity)
 

<pre lang="markdown"> ## Project Structure ```
flask-mvc-smart-calculator/
    │
    ├── calculator_app/
    │   │
    |   ├── __pycache__/              
    │   ├── main.py                     
    │   ├── config.py                  
    │   ├── factory.py
    │   ├── logging_config.py           
    │   │
    │   ├── app/
    │   │   │
    │   │   ├── __init__.py             
    │   │   ├── extensions.py           
    │   │   │
    │   │   ├── auth/
    │   │   │   ├── __init__.py
    │   │   │   └── manager.py
    │   │   │
    │   │   ├── cache/
    │   │   │   ├── __init__.py
    │   │   │   └── expression_cache.py
    │   │   │
    │   │   ├── db/
    │   │   │   ├── __init__.py
    │   │   │   └── manager.py
    │   │   │
    │   │   ├── core/
    │   │   │   ├── __init__.py
    │   │   │   ├── model.py
    │   │   │   └── controller.py
    │   │   │
    │   │   ├── widgets/
    │   │   │   ├── __init__.py
    │   │   │   └── ui.py
    │   │   │
    │   │   ├── routes/
    │   │   │   ├── __init__.py
    │   │   │   ├── api.py
    │   │   │   └── web.py
    │   │   │
    │   │   └── templates/
    │   │       └── index.html
    │   │
    |   |
    │   └── data/
    │   │   └── calculator_api.db
    │   │
    │   └── python_calculator/          # for mathematical expressions
    │       └── calculator.py
    │       └── ClassEva.py
    |
    ├── logs/                    # log directory
    │   ├── calculations.log
    │   ├── calculator_app.log
    │   └── errors.log
    |
    ├── compose.yaml             # Config Docker Compose
    ├── dockerfile               # Dockerfile for containerization
    ├── requirements.txt         # Python dependencies
    ├── test_api_script.py       # API test script (automation)
    ├── README.md
``` </pre>

Key Features
1. Authentication
    Predefined users: admin / user

    Passwords are hashed using SHA-256

    Session persistence in .auth_state.json

    CLI-based authentication and support for environment variables in container mode

2. Operations
    Three types of calculations are supported:

    calculator – mathematical expressions (e.g., 2+2, sqrt(16))

    fibonacci – the n-th Fibonacci number

    factorial – the factorial of an integer

3. Caching
    Results are cached in memory for speed

    Types: calculator, fibonacci, factorial

    Statistics available via /api/cache/stats

    Dedicated endpoint for clearing: /api/cache/clear

4. Persistence via SQLite
    Two tables:

        api_requests: logs for every API request (with timestamp, IP, user-agent, etc.)

        user_sessions: stores the user's last selection and input

5. Complete RESTful API
    POST /api/calculate – main endpoint

    POST /api/calculator, /api/fibonacci, /api/factorial – specialized endpoints

    GET /api/health – health check

    GET /api/history – request history

    GET /api/analytics – usage statistics

    GET /api/cache/stats, POST /api/cache/clear – cache management

Automated Testing – test_api_script.py
    This script includes:

    Health check tests (/api/health)

    History verification (/api/history)

    Analytics validation (/api/analytics)

    Cache functionality tests (hit/miss)

    Endpoint-specific validation

Running the script confirms the full functionality of the application.

Web Interface (HTML Template)
Minimalist web UI with:

    Three output boxes (calculator, fibonacci, factorial)

    Radio button group for selecting the operation

    Text area for input

    &Return button (form submission)

    Results are dynamically displayed on screen

Each component has an associated Python class: MyDisplayBox, MyReturnButton, MyEditBox, MyRadioGroup

Dockerization
    dockerfile (assumed content)
    Includes standard steps:

    Copy source code

    Install dependencies (requirements.txt)

    Expose ports

    Run calculator_app.main

compose.yaml
Runs the application with:

    Flask binds to 0.0.0.0:5000 inside the container, which allows external access.
    You should open http://localhost:5000 in your browser.

    Volumes for data/ and logs/ for persistence

    **Automatic Role:** When running via Docker, the application is configured to bypass manual CLI login and **automatically run with the `user` role** using environment variables (`CONTAINER_USERNAME` and `CONTAINER_PASSWORD`).

Running the Project

To build and start the application using Docker, run:

    docker compose up --build

This command will:

    build the Docker image
    start all services defined in compose.yaml
    expose the application on http://localhost:5000
