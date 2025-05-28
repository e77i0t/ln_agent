# Company Research Tool

A Flask-based web application for researching companies using various data sources.

## Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose
- Git

## Project Structure

```
./
├── .env.example          # Example environment variables
├── .gitignore           # Git ignore file
├── requirements.txt     # Main project dependencies
├── requirements-dev.txt # Development dependencies
├── docker-compose.yml  # Docker services configuration
├── config.py          # Application configuration
├── app/              # Main application package
│   ├── __init__.py
│   ├── config.py
│   └── utils/
│       ├── __init__.py
│       └── logger.py
├── tests/           # Test suite
│   ├── __init__.py
│   └── conftest.py
└── scripts/        # Development and utility scripts
    └── setup_dev.py
```

## Getting Started

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd company_research_tool
   ```

2. Run the development setup script:
   ```bash
   python scripts/setup_dev.py
   ```
   This script will:
   - Check Python version
   - Create a virtual environment
   - Install dependencies
   - Set up environment variables
   - Start Docker services (MongoDB and Redis)

3. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

4. Start the development server:
   ```bash
   flask run
   ```

## Development

### Environment Variables

Copy the example environment file and modify as needed:
```bash
cp env.example .env
```

Key environment variables:
- `FLASK_ENV`: Set to 'development' for development mode
- `MONGODB_URI`: MongoDB connection string
- `REDIS_URL`: Redis connection string
- `API_KEY_1`, `API_KEY_2`: API keys for external services

### Docker Services

The project uses Docker Compose to manage:
- MongoDB (port 27017)
- Redis (port 6379)

Start services:
```bash
docker compose up -d
```

Stop services:
```bash
docker compose down
```

### Testing

Run tests with pytest:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=app tests/
```

### Code Style

The project uses:
- Black for code formatting
- Flake8 for linting

Format code:
```bash
black .
```

Run linter:
```bash
flake8
```

## License

[Your License Here]