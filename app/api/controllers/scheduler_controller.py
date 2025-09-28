from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.hotel_entities import Hotel, HotelAmenity, HotelImage
from app.services.scheduler_service import scheduler_service
from app.core.logger import logger
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/api/scheduler", tags=["Scheduler Management"])

@router.get("/status", summary="Get Scheduler Status")
async def get_scheduler_status():
    """
    Get current scheduler status and job information
    
    Returns:
    - Scheduler running status
    - Total number of jobs
    - Job statistics and execution details
    """
    try:
        stats = scheduler_service.get_scheduler_health()
        return {
            "status": "success",
            "data": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting scheduler status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get scheduler status: {str(e)}")

@router.get("/jobs", summary="Get All Scheduled Jobs")
async def get_scheduled_jobs():
    """
    Get detailed information about all scheduled jobs
    
    Returns:
    - List of all scheduled jobs
    - Job execution schedules
    - Job statistics and performance metrics
    """
    try:
        if not scheduler_service.scheduler:
            return {
                "status": "error",
                "message": "Scheduler not initialized",
                "jobs": []
            }
        
        jobs = scheduler_service.scheduler.get_jobs()
        job_details = []
        
        for job in jobs:
            job_info = {
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger),
                "func": job.func.__name__ if job.func else "Unknown",
                "args": job.args,
                "kwargs": job.kwargs
            }
            job_details.append(job_info)
        
        return {
            "status": "success",
            "total_jobs": len(job_details),
            "jobs": job_details,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting scheduled jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get scheduled jobs: {str(e)}")

@router.get("/stats", summary="Get Scheduler Statistics")
async def get_scheduler_statistics():
    """
    Get comprehensive scheduler statistics and performance metrics
    
    Returns:
    - Job execution statistics
    - Performance metrics
    - Error rates and success rates
    """
    try:
        stats = scheduler_service.get_scheduler_health()
        job_stats = stats.get('job_stats', {})
        
        # Calculate summary statistics
        total_jobs = len(job_stats)
        successful_jobs = sum(1 for job in job_stats.values() if job.get('status') == 'completed')
        failed_jobs = sum(1 for job in job_stats.values() if job.get('status') == 'error')
        
        # Calculate total hotels processed
        total_hotels_processed = sum(job.get('hotels_processed', 0) for job in job_stats.values())
        total_hotels_updated = sum(job.get('hotels_updated', 0) for job in job_stats.values())
        total_hotels_created = sum(job.get('hotels_created', 0) for job in job_stats.values())
        
        return {
            "status": "success",
            "data": {
                "scheduler_status": stats.get('status', 'unknown'),
                "total_jobs": total_jobs,
                "successful_jobs": successful_jobs,
                "failed_jobs": failed_jobs,
                "success_rate": (successful_jobs / total_jobs * 100) if total_jobs > 0 else 0,
                "total_hotels_processed": total_hotels_processed,
                "total_hotels_updated": total_hotels_updated,
                "total_hotels_created": total_hotels_created,
                "job_details": job_stats
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting scheduler statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get scheduler statistics: {str(e)}")

@router.get("/database/stats", summary="Get Database Statistics")
async def get_database_statistics(db: Session = Depends(get_db)):
    """
    Get current database statistics showing data being updated
    
    Returns:
    - Total counts of hotels, amenities, images
    - Recent update statistics
    - Data freshness metrics
    """
    try:
        # Get total counts
        total_hotels = db.query(Hotel).count()
        total_amenities = db.query(HotelAmenity).count()
        total_images = db.query(HotelImage).count()
        
        # Get recent updates (last hour)
        hour_cutoff = datetime.utcnow() - timedelta(hours=1)
        hourly_hotels = db.query(Hotel).filter(Hotel.updated_at >= hour_cutoff).count()
        
        # Get recent updates (last 24 hours)
        day_cutoff = datetime.utcnow() - timedelta(days=1)
        daily_hotels = db.query(Hotel).filter(Hotel.updated_at >= day_cutoff).count()
        
        # Get hotels updated in last 5 minutes
        recent_cutoff = datetime.utcnow() - timedelta(minutes=5)
        recent_hotels = db.query(Hotel).filter(Hotel.updated_at >= recent_cutoff).count()
        
        # Get most recently updated hotels
        recent_hotel_list = db.query(Hotel).filter(
            Hotel.updated_at.isnot(None)
        ).order_by(Hotel.updated_at.desc()).limit(10).all()
        
        recent_updates = []
        for hotel in recent_hotel_list:
            recent_updates.append({
                "id": hotel.id,
                "name": hotel.name,
                "city": hotel.city,
                "state": hotel.state,
                "country": hotel.country,
                "updated_at": hotel.updated_at.isoformat() if hotel.updated_at else None,
                "star_rating": hotel.star_rating,
                "avg_rating": hotel.avg_rating
            })
        
        return {
            "status": "success",
            "data": {
                "total_counts": {
                    "hotels": total_hotels,
                    "amenities": total_amenities,
                    "images": total_images
                },
                "recent_activity": {
                    "last_5_minutes": recent_hotels,
                    "last_hour": hourly_hotels,
                    "last_24_hours": daily_hotels
                },
                "recent_updates": recent_updates,
                "data_freshness": {
                    "last_updated": recent_updates[0]["updated_at"] if recent_updates else None,
                    "is_active": recent_hotels > 0
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting database statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get database statistics: {str(e)}")

@router.get("/recent-updates", summary="Get Recent Hotel Updates")
async def get_recent_updates(
    limit: int = Query(20, ge=1, le=100, description="Number of recent updates to return"),
    hours_back: int = Query(24, ge=1, le=168, description="Hours to look back for updates"),
    db: Session = Depends(get_db)
):
    """
    Get recent hotel updates showing what data is being refreshed
    
    Returns:
    - List of recently updated hotels
    - Update timestamps
    - Hotel details and location information
    """
    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        
        recent_hotels = db.query(Hotel).filter(
            Hotel.updated_at >= cutoff_time
        ).order_by(Hotel.updated_at.desc()).limit(limit).all()
        
        updates = []
        for hotel in recent_hotels:
            updates.append({
                "id": hotel.id,
                "name": hotel.name,
                "description": hotel.description,
                "address": hotel.address,
                "city": hotel.city,
                "state": hotel.state,
                "country": hotel.country,
                "latitude": hotel.latitude,
                "longitude": hotel.longitude,
                "star_rating": hotel.star_rating,
                "avg_rating": hotel.avg_rating,
                "total_reviews": hotel.total_reviews,
                "updated_at": hotel.updated_at.isoformat() if hotel.updated_at else None,
                "created_at": hotel.created_at.isoformat() if hotel.created_at else None
            })
        
        return {
            "status": "success",
            "data": {
                "total_updates": len(updates),
                "time_range_hours": hours_back,
                "updates": updates
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting recent updates: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get recent updates: {str(e)}")

@router.post("/refresh/{city_name}", summary="Trigger Manual Refresh")
async def trigger_manual_refresh(
    city_name: str,
    state: Optional[str] = Query(None, description="State name"),
    country: Optional[str] = Query(None, description="Country name"),
    db: Session = Depends(get_db)
):
    """
    Manually trigger hotel refresh for a specific city
    
    This will immediately start refreshing hotel data for the specified city
    instead of waiting for the scheduled time.
    """
    try:
        result = scheduler_service.trigger_manual_refresh(city_name, state, country)
        return {
            "status": "success",
            "message": f"Manual refresh triggered for {city_name}",
            "data": result,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error triggering manual refresh: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger manual refresh: {str(e)}")

@router.get("/schedule", summary="Get Scheduler Schedule")
async def get_scheduler_schedule():
    """
    Get the scheduler schedule showing when each city is refreshed
    
    Returns:
    - City refresh schedules
    - Demand levels and intervals
    - Next scheduled refresh times
    """
    try:
        import json
        from pathlib import Path
        
        config_file = Path(__file__).parent.parent.parent / "config" / "city_demand_config.json"
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        schedule_info = []
        for demand_level, level_config in config['city_demand_levels'].items():
            cities = level_config['cities']
            interval = level_config['refresh_interval_minutes']
            
            city_list = []
            for city in cities:
                city_list.append({
                    "name": city['name'],
                    "state": city['state'],
                    "country": city['country']
                })
            
            schedule_info.append({
                "demand_level": demand_level,
                "refresh_interval_minutes": interval,
                "cities_count": len(cities),
                "cities": city_list
            })
        
        return {
            "status": "success",
            "data": {
                "schedule": schedule_info,
                "scheduler_settings": config.get('scheduler_settings', {}),
                "refresh_settings": config.get('refresh_settings', {})
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting scheduler schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get scheduler schedule: {str(e)}")

@router.get("/dashboard", summary="Get Scheduler Dashboard Data")
async def get_scheduler_dashboard(db: Session = Depends(get_db)):
    """
    Get comprehensive dashboard data for monitoring scheduler activity
    
    This endpoint provides all the data needed for a real-time dashboard
    showing scheduler status, database updates, and performance metrics.
    """
    try:
        # Get scheduler status
        scheduler_stats = scheduler_service.get_scheduler_health()
        
        # Get database statistics
        total_hotels = db.query(Hotel).count()
        total_amenities = db.query(HotelAmenity).count()
        total_images = db.query(HotelImage).count()
        
        # Get recent activity
        hour_cutoff = datetime.utcnow() - timedelta(hours=1)
        recent_hotels = db.query(Hotel).filter(Hotel.updated_at >= hour_cutoff).count()
        
        # Get recent updates
        recent_updates = db.query(Hotel).filter(
            Hotel.updated_at.isnot(None)
        ).order_by(Hotel.updated_at.desc()).limit(5).all()
        
        recent_updates_list = []
        for hotel in recent_updates:
            recent_updates_list.append({
                "id": hotel.id,
                "name": hotel.name,
                "city": hotel.city,
                "updated_at": hotel.updated_at.isoformat() if hotel.updated_at else None
            })
        
        return {
            "status": "success",
            "data": {
                "scheduler": {
                    "status": scheduler_stats.get('status', 'unknown'),
                    "total_jobs": scheduler_stats.get('total_jobs', 0),
                    "is_running": scheduler_stats.get('status') == 'running'
                },
                "database": {
                    "total_hotels": total_hotels,
                    "total_amenities": total_amenities,
                    "total_images": total_images,
                    "recent_updates_last_hour": recent_hotels
                },
                "recent_activity": recent_updates_list,
                "last_updated": datetime.utcnow().isoformat()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting dashboard data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard data: {str(e)}")
