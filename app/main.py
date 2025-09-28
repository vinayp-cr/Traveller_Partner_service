from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.api.controllers import hotel_controller, search_filters_controller, search_filters_controller_consolidated, scheduler_controller, filter_data_controller, auth_controller, data_population_controller, hotel_filter_controller, terrapay_webhook_controller
from app.ai.chatbot.controllers.chat_controller import router as chat_router
from app.utilities.message_loader import message_loader
from app.services.scheduler_service import scheduler_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events"""
    # Startup
    try:
        scheduler_service.start_scheduler()
        print("Hotel scheduler service started")
    except Exception as e:
        print(f"Failed to start scheduler: {e}")
    
    yield
    
    # Shutdown
    try:
        scheduler_service.stop_scheduler()
        print("Hotel scheduler service stopped")
    except Exception as e:
        print(f"Error stopping scheduler: {e}")


app = FastAPI(
    title=message_loader.get_service_info("name"),
    version=message_loader.get_service_info("version"),
    description=message_loader.get_service_info("description"),
    lifespan=lifespan
)

# add cors middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": message_loader.get_health_info("status"),
        "service": message_loader.get_health_info("service")
    }

# register controllers
app.include_router(hotel_controller.router)
app.include_router(search_filters_controller.router)
app.include_router(search_filters_controller_consolidated.router)
app.include_router(scheduler_controller.router)
app.include_router(filter_data_controller.router)
app.include_router(auth_controller.router)
app.include_router(data_population_controller.router, prefix="/api/data", tags=["Data Population"])
app.include_router(hotel_filter_controller.router, prefix="/api/hotel", tags=["Hotel Filtering"])
app.include_router(terrapay_webhook_controller.router, prefix="/api", tags=["TerraPay Webhooks"])

# Include chatbot routes
app.include_router(chat_router, tags=["Chatbot"])

# Serve static files (dashboard and chatbot)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/ai/static", StaticFiles(directory="app/ai/static"), name="ai_static")

# Dashboard endpoint
@app.get("/dashboard", summary="Scheduler Dashboard")
async def get_dashboard():
    """Get the scheduler monitoring dashboard"""
    from fastapi.responses import FileResponse
    return FileResponse("app/static/dashboard.html")

# Chatbot interface endpoint
@app.get("/chatbot", summary="Chatbot Interface")
async def get_chatbot():
    """Get the chatbot interface"""
    from fastapi.responses import FileResponse
    return FileResponse("app/ai/static/chatbot/chatbot.html")
