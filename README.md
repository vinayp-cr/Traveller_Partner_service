# Xeni Hotelier Integration Services

A FastAPI-based microservice that provides integration with Xeni Hotel APIs for hotel search, autosuggest, rooms and rates, price recommendations, and booking functionality.

## 🏨 Features

### Core Functionality

- **Hotel Autosuggest API** - Get hotel suggestions based on text input
- **Hotel Search API** - Search for hotels with advanced filtering options
- **Rooms and Rates API** - Retrieve available rooms and pricing information
- **Price Recommendation API** - Get price recommendations for specific hotels
- **Hotel Booking API** - Complete hotel booking process

### API Endpoints

| Endpoint | Method | Description | Tags |
|----------|--------|-------------|------|
| `/api/hotel/autosuggest` | POST | Hotel autosuggest functionality | Hotel Autosuggest |
| `/api/hotel/search` | POST | Hotel search with filters | Hotel Search |
| `/api/hotel/roomsandrates` | POST | Get rooms and rates | Hotel Rooms and Rates |
| `/api/hotel/{hotel_id}/{api_token}/price/recommendation/{recommendation_id}` | GET | Price recommendations | Hotel Price Recommendation |
| `/api/hotel/book/{hotel_id}/{session_id}` | POST | Hotel booking | Hotel Booking |

## 🛠️ Technology Stack

- **Framework**: FastAPI (Python 3.8+)
- **HTTP Client**: Requests library
- **Data Validation**: Pydantic models
- **Environment Management**: python-dotenv
- **CORS**: FastAPI CORS middleware

## 📋 Dependencies

### Core Dependencies

The project uses the following main dependencies:

- **FastAPI**: Modern, fast web framework for building APIs
- **Pydantic**: Data validation using Python type annotations
- **Requests**: HTTP library for making API calls
- **python-dotenv**: Environment variable management

### Development Dependencies

- **Uvicorn**: ASGI server for running FastAPI applications

## 📦 Installation & Setup

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git
- Docker and Docker Compose (for containerized deployment)

### Option 1: Local Development Setup

#### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd TravelPartnerServices
```

#### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

#### Step 4: Environment Configuration

Create a `.env` file in the root directory:

```env
XENI_API_KEY=your_xeni_api_key_here
```

**Note**: You need to obtain a valid Xeni API key to use the services.

#### Step 5: Run the Application

```bash
# Development mode
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

## 🐳 Containerization Features

This application is fully containerized with Docker, providing consistent deployment across different environments.

### Docker Components

- **Dockerfile**: Development container with hot-reload support
- **Dockerfile.prod**: Multi-stage production build with optimized layers
- **docker-compose.yml**: Development environment with volume mounting
- **docker-compose.prod.yml**: Production environment with resource limits
- **Makefile**: Convenient commands for Docker operations

### Containerization Benefits

- **Consistency**: Same environment across development, staging, and production
- **Isolation**: Application runs in isolated containers with its own dependencies
- **Scalability**: Easy to scale horizontally with multiple container instances
- **Portability**: Deploy anywhere Docker is supported
- **Security**: Non-root user execution and minimal attack surface
- **Resource Management**: Built-in resource limits and health checks

### Health Monitoring

The containerized application includes:
- Health check endpoint at `/health`
- Docker health checks with configurable intervals
- Resource usage monitoring
- Automatic restart policies

### Option 2: Docker Containerization (Recommended)

#### Prerequisites for Docker

- Docker installed on your system
- Docker Compose installed
- Make (optional, for using Makefile commands)

#### Step 1: Clone and Setup Environment

```bash
git clone <repository-url>
cd TravelPartnerServices

# Copy environment template
cp env.example .env

# Edit .env file with your Xeni API key
XENI_API_KEY=your_actual_api_key_here
```

#### Step 2: Development Mode with Docker

```bash
# Build and run the application
docker-compose up -d

# Or use Makefile commands (if Make is installed)
make build
make run

# Check logs
docker-compose logs -f app
# or
make logs

# Stop the application
docker-compose down
# or
make stop
```

#### Step 3: Production Mode with Docker

```bash
# Build and run production version
docker-compose -f docker-compose.prod.yml up -d

# Or use Makefile commands
make build-prod
make run-prod

# Check production logs
docker-compose -f docker-compose.prod.yml logs -f app
# or
make logs-prod

# Stop production application
docker-compose -f docker-compose.prod.yml down
# or
make stop-prod
```

#### Step 4: Access the Containerized Application

- **Development**: `http://localhost:8000`
- **Production**: `http://localhost:8000`
- **Health Check**: `http://localhost:8000/health`
- **API Documentation**: `http://localhost:8000/docs`

#### Docker Management Commands

```bash
# View all available Makefile commands
make help

# Clean up Docker resources
make clean

# Access container shell
make shell

# Run tests in container
make test
```

#### Manual Docker Commands

```bash
# Build images
docker build -t xeni-hotelier-api:dev .
docker build -f Dockerfile.prod -t xeni-hotelier-api:prod .

# Run containers
docker run -d --name xeni-hotelier-api -p 8000:8000 --env-file .env xeni-hotelier-api:dev
docker run -d --name xeni-hotelier-api-prod -p 8000:8000 --env-file .env --memory=512m --cpus=0.5 xeni-hotelier-api:prod

# Check container status
docker ps -a
docker logs <container_name>
```

## 📚 API Documentation

Once the application is running, you can access:

- **Interactive API Docs**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

## 🔧 Configuration

The application configuration is managed through `app/core/config.py`:

- **XENI_AUTOCOMPLETE_API_URL**: Hotel autosuggest API endpoint
- **XENI_HOTEL_SEARCH_API_URL**: Hotel search API endpoint
- **XENI_ROOMS_AND_RATES_API_URL**: Rooms and rates API endpoint
- **XENI_BASE_URL**: Base URL for Xeni APIs
- **XENI_API_KEY**: API key for authentication (from environment variables)

## 📁 Project Structure

```
TravelPartnerServices/
├── app/
│   ├── api/
│   │   ├── controllers/
│   │   │   └── hotel_controller.py      # API route definitions
│   │   └── services/
│   │       └── hotel_service.py         # Business logic implementation
│   ├── core/
│   │   └── config.py                    # Configuration settings
│   ├── models/                          # Pydantic data models
│   │   ├── autosuggest_request.py
│   │   ├── autosuggest_response.py
│   │   ├── booking_model.py
│   │   ├── hotel_search_models.py
│   │   └── rooms_and_rates_request.py
│   ├── utilities/
│   │   └── http_client.py               # HTTP client utilities
│   └── main.py                          # FastAPI application entry point
├── requirements.txt                      # Python dependencies
└── README.md                            # This file
```

## 🚀 Usage Examples

### Hotel Autosuggest

```bash
curl -X POST "http://localhost:8000/api/hotel/autosuggest" \
  -H "Content-Type: application/json" \
  -H "Accept-Language: en" \
  -d '{"text": "New York"}'
```

### Hotel Search

```bash
curl -X POST "http://localhost:8000/api/hotel/search?page=1&limit=10" \
  -H "Content-Type: application/json" \
  -H "Accept-Language: en" \
  -d '{
    "checkInDate": "2024-01-15",
    "checkOutDate": "2024-01-17",
    "lat": 40.7128,
    "lng": -74.0060,
    "nationality": "US",
    "type": "leisure",
    "occupancies": [{"noOfRoom": 1, "adults": 2}],
    "currency": "USD"
  }'
```

## 🔒 Security

- API key authentication through `X-API-Key` header
- CORS middleware configured for cross-origin requests
- Input validation using Pydantic models
- Error handling with proper HTTP status codes

## 🧪 Testing

To run tests (when implemented):

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

## 🔧 Docker Troubleshooting

### Common Docker Issues

1. **Port Already in Use**
   ```bash
   # Change port in docker-compose.yml
   ports:
     - "8002:8000"  # Use different host port
   ```

2. **Permission Denied**
   ```bash
   # Ensure Docker has proper permissions
   sudo usermod -aG docker $USER
   # Restart Docker service
   ```

3. **Build Fails**
   ```bash
   # Clean and rebuild
   make clean
   make build
   
   # Check Docker logs
   docker-compose logs app
   ```

4. **Container Won't Start**
   ```bash
   # Check container status
   docker ps -a
   
   # View detailed logs
   docker logs <container_name>
   
   # Check resource usage
   docker stats <container_name>
   ```

### Debugging Commands

```bash
# Access container shell
make shell

# Check container health
docker inspect <container_name> | grep Health -A 10

# View container processes
docker exec <container_name> ps aux

# Check network connectivity
docker network ls
docker network inspect xeni-network
```

### Cleanup Commands

```bash
# Remove all containers and images
make clean

# Manual cleanup
docker-compose down -v --rmi all
docker system prune -f
docker volume prune -f
```

## 📝 Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `XENI_API_KEY` | Xeni API authentication key | Yes | None |

## 🚨 Error Handling

The application includes comprehensive error handling:

- HTTP 500 errors for internal server errors
- Proper exception handling with detailed error messages
- Correlation ID tracking for debugging
- Session ID management for booking flows

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 🚀 Production Deployment

### Production Docker Features

The production Docker setup includes several optimizations:

- **Multi-stage Build**: Reduces final image size by excluding build dependencies
- **Resource Limits**: Memory and CPU constraints for predictable performance
- **Security**: Non-root user execution and minimal attack surface
- **Health Checks**: Built-in monitoring for load balancer integration
- **Optimized Layers**: Efficient Docker layer caching for faster builds

### Production Environment Variables

```bash
# Required
XENI_API_KEY=your_production_api_key

# Optional (with defaults)
PYTHONPATH=/app
```

### Production Resource Limits

```yaml
# From docker-compose.prod.yml
deploy:
  resources:
    limits:
      memory: 512M
      cpus: '0.5'
    reservations:
      memory: 256M
      cpus: '0.25'
```

### Production Health Monitoring

```bash
# Health check endpoint
GET /health

# Docker health check configuration
healthcheck:
  test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/health')"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### Scaling in Production

```bash
# Scale to multiple instances
docker-compose -f docker-compose.prod.yml up -d --scale app=3

# Load balancer integration
# Use the health check endpoint for health monitoring
# Configure your load balancer to check /health endpoint
```

## 📄 License

## 🆘 Support

For support and questions:

- Create an issue in the repository
- Contact the development team
- Check the API documentation at `/docs`

## 🔄 Version History

- **v1.0.0**: Initial release with core hotel integration services