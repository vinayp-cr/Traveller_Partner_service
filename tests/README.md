# Hotel Controller Integration Tests

This test suite provides comprehensive integration testing for the hotel search functionality, testing the complete flow from controller to service to repository with real API calls.

## Test Structure

### Test Files
- `test_hotel_controller_integration.py` - Main integration test file

### Test Configuration
- `pytest.ini` - Pytest configuration
- `run_tests.py` - Test runner script

## Test Coverage

### 1. `test_hotel_search_integration`
- **Purpose**: Tests the complete integration flow
- **Flow**: Controller → Service → Repository → External Xeni API
- **What it tests**:
  - Real API calls to Xeni hotel search endpoint
  - Database operations (if hotels are found)
  - Error handling for API failures
  - Service method functionality

### 2. `test_hotel_search_controller_endpoint`
- **Purpose**: Tests the FastAPI endpoint
- **What it tests**:
  - HTTP endpoint functionality
  - Request/response handling
  - Error response structure

### 3. `test_hotel_search_with_different_criteria`
- **Purpose**: Tests with different search parameters
- **What it tests**:
  - Different city coordinates (London)
  - Different occupancy configurations
  - Service method with varied inputs

### 4. `test_database_connection`
- **Purpose**: Verifies database connectivity
- **What it tests**:
  - SQLite database connection
  - Basic SQL query execution

## Running Tests

### Option 1: Using the test runner
```bash
python run_tests.py
```

### Option 2: Using pytest directly
```bash
pytest tests/test_hotel_controller_integration.py -v -s
```

### Option 3: Run specific test
```bash
pytest tests/test_hotel_controller_integration.py::TestHotelControllerIntegration::test_hotel_search_integration -v -s
```

## Test Data

The tests use realistic hotel search data:
- **New York**: lat=40.7128, lng=-74.0060
- **London**: lat=51.5074, lng=-0.1278
- **Occupancy**: Various adult/children configurations
- **Dates**: Future dates for realistic searches

## Expected Behavior

### Success Scenarios
- If Xeni API returns hotels, they should be saved to database
- Database connection should work properly
- Endpoints should respond correctly

### Error Scenarios
- API failures (404, network issues) are handled gracefully
- Invalid requests return appropriate error responses
- Service errors are properly caught and reported

## Integration Testing Philosophy

These tests are designed for **real integration testing** without mocking:
- ✅ Real API calls to Xeni
- ✅ Real database operations
- ✅ Real error handling
- ✅ Full request/response cycle

This approach ensures that:
1. The integration actually works end-to-end
2. API changes are caught early
3. Database operations function correctly
4. Error handling is robust

## Notes

- Tests may fail if Xeni API is unavailable (this is expected)
- Database uses SQLite for testing (no external DB required)
- Tests are designed to be resilient to API failures
- All tests should pass even if external APIs are down
