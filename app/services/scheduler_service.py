import json
import os
from pathlib import Path
from typing import Dict, List, Any
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.api.services.hotel_service import HotelService
from app.services.hotel_refresh_service import HotelRefreshService
from app.models.hotel_search_models import HotelSearchRequest
from app.core.logger import logger
import traceback
from datetime import datetime


class HotelSchedulerService:
    """
    Service class for managing scheduled hotel data refresh jobs.
    Uses APScheduler to run staggered background jobs based on city demand levels.
    """
    
    def __init__(self):
        self.scheduler = None
        self.hotel_service = HotelService()
        self.hotel_refresh_service = HotelRefreshService()
        self.config = self._load_city_config()
        self.job_stats = {}
        
    def _load_city_config(self) -> Dict[str, Any]:
        """Load city demand configuration from JSON file"""
        try:
            config_file = Path(__file__).parent.parent / "config" / "city_demand_config.json"
            with open(config_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load city configuration: {str(e)}")
            raise e
    
    def start_scheduler(self):
        """Initialize and start the background scheduler"""
        try:
            # Configure job stores and executors
            jobstores = {
                'default': MemoryJobStore()
            }
            
            executors = {
                'default': ThreadPoolExecutor(max_workers=self.config['scheduler_settings']['max_workers'])
            }
            
            job_defaults = self.config['scheduler_settings']['job_defaults']
            
            # Create scheduler
            self.scheduler = BackgroundScheduler(
                jobstores=jobstores,
                executors=executors,
                job_defaults=job_defaults,
                timezone=self.config['scheduler_settings']['timezone']
            )
            
            # Add event listeners
            self.scheduler.add_listener(self._job_executed_listener, EVENT_JOB_EXECUTED)
            self.scheduler.add_listener(self._job_error_listener, EVENT_JOB_ERROR)
            
            # Add jobs for each city based on demand level
            self._add_city_jobs()
            
            # Start the scheduler
            self.scheduler.start()
            logger.info("Hotel scheduler service started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start scheduler: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise e
    
    def stop_scheduler(self):
        """Stop the background scheduler"""
        try:
            if self.scheduler and self.scheduler.running:
                self.scheduler.shutdown(wait=True)
                logger.info("Hotel scheduler service stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {str(e)}")
    
    def _add_city_jobs(self):
        """Add scheduled jobs for each city based on demand level"""
        try:
            city_demand_levels = self.config['city_demand_levels']
            
            for demand_level, level_config in city_demand_levels.items():
                interval_minutes = level_config['refresh_interval_minutes']
                cities = level_config['cities']
                
                for city in cities:
                    city_name = city['name']
                    state = city.get('state', '')
                    country = city.get('country', '')
                    
                    # Create job ID
                    job_id = f"refresh_hotels_{city_name}_{state}_{country}".replace(" ", "_").lower()
                    
                    # Add job with city-specific parameters
                    self.scheduler.add_job(
                        func=self._refresh_hotels_for_city,
                        trigger='interval',
                        minutes=interval_minutes,
                        id=job_id,
                        args=[city_name, state, country, demand_level],
                        replace_existing=True,
                        max_instances=1
                    )
                    
                    logger.info(f"Added job for {city_name}, {state}, {country} - {demand_level} demand (every {interval_minutes} minutes)")
            
            logger.info(f"Total jobs added: {len(self.scheduler.get_jobs())}")
            
        except Exception as e:
            logger.error(f"Failed to add city jobs: {str(e)}")
            raise e
    
    def _refresh_hotels_for_city(self, city_name: str, state: str, country: str, demand_level: str):
        """
        Refresh hotel data for a specific city.
        This method is called by the scheduler for each city.
        """
        job_id = f"refresh_hotels_{city_name}_{state}_{country}".replace(" ", "_").lower()
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Starting hotel refresh for {city_name}, {state}, {country} ({demand_level} demand)")
            
            # Get database session
            db = next(get_db())
            
            try:
                # Use the hotel refresh service for comprehensive data refresh
                refresh_result = self.hotel_refresh_service.refresh_hotels_for_city(
                    db, city_name, state, country
                )
                
                # Update job statistics
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                self.job_stats[job_id] = {
                    'last_execution': start_time.isoformat(),
                    'execution_time_seconds': execution_time,
                    'hotels_processed': refresh_result.get('hotels_processed', 0),
                    'hotels_updated': refresh_result.get('hotels_updated', 0),
                    'hotels_created': refresh_result.get('hotels_created', 0),
                    'amenities_updated': refresh_result.get('amenities_updated', 0),
                    'images_updated': refresh_result.get('images_updated', 0),
                    'status': refresh_result.get('status', 'unknown'),
                    'demand_level': demand_level,
                    'errors': refresh_result.get('errors', [])
                }
                
                logger.info(f"Successfully refreshed {refresh_result.get('hotels_processed', 0)} hotels for {city_name}, {state}, {country} in {execution_time:.2f} seconds")
                
            finally:
                db.close()
                
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            error_msg = f"Error refreshing hotels for {city_name}, {state}, {country}: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Update job statistics with error
            self.job_stats[job_id] = {
                'last_execution': start_time.isoformat(),
                'execution_time_seconds': execution_time,
                'hotels_processed': 0,
                'status': 'error',
                'error_message': str(e),
                'demand_level': demand_level
            }
    
    def _job_executed_listener(self, event):
        """Listener for successful job execution"""
        job_id = event.job_id
        logger.debug(f"Job {job_id} executed successfully")
    
    def _job_error_listener(self, event):
        """Listener for job execution errors"""
        job_id = event.job_id
        exception = event.exception
        logger.error(f"Job {job_id} failed with exception: {str(exception)}")
    
    def get_job_status(self) -> Dict[str, Any]:
        """Get current status of all scheduled jobs"""
        try:
            jobs = self.scheduler.get_jobs() if self.scheduler else []
            
            job_status = {
                'scheduler_running': self.scheduler.running if self.scheduler else False,
                'total_jobs': len(jobs),
                'jobs': []
            }
            
            for job in jobs:
                job_info = {
                    'job_id': job.id,
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger),
                    'args': job.args
                }
                
                # Add statistics if available
                if job.id in self.job_stats:
                    job_info.update(self.job_stats[job.id])
                
                job_status['jobs'].append(job_info)
            
            return job_status
            
        except Exception as e:
            logger.error(f"Error getting job status: {str(e)}")
            return {'error': str(e)}
    
    def trigger_manual_refresh(self, city_name: str, state: str = None, country: str = None) -> Dict[str, Any]:
        """Manually trigger a hotel refresh for a specific city"""
        try:
            # Find the demand level for this city
            demand_level = self._find_city_demand_level(city_name, state, country)
            
            if not demand_level:
                return {
                    'success': False,
                    'message': f'City {city_name}, {state}, {country} not found in configuration'
                }
            
            # Trigger the refresh
            self._refresh_hotels_for_city(city_name, state or '', country or '', demand_level)
            
            return {
                'success': True,
                'message': f'Manual refresh triggered for {city_name}, {state}, {country}',
                'demand_level': demand_level
            }
            
        except Exception as e:
            logger.error(f"Error in manual refresh: {str(e)}")
            return {
                'success': False,
                'message': f'Error triggering manual refresh: {str(e)}'
            }
    
    def _find_city_demand_level(self, city_name: str, state: str = None, country: str = None) -> str:
        """Find the demand level for a specific city"""
        try:
            city_demand_levels = self.config['city_demand_levels']
            
            for demand_level, level_config in city_demand_levels.items():
                cities = level_config['cities']
                
                for city in cities:
                    if (city['name'].lower() == city_name.lower() and
                        (not state or city.get('state', '').lower() == state.lower()) and
                        (not country or city.get('country', '').lower() == country.lower())):
                        return demand_level
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding city demand level: {str(e)}")
            return None
    
    def get_scheduler_health(self) -> Dict[str, Any]:
        """Get scheduler health information"""
        try:
            if not self.scheduler:
                return {
                    'status': 'not_initialized',
                    'message': 'Scheduler not initialized'
                }
            
            return {
                'status': 'running' if self.scheduler.running else 'stopped',
                'message': 'Scheduler is running' if self.scheduler.running else 'Scheduler is stopped',
                'total_jobs': len(self.scheduler.get_jobs()),
                'job_stats': self.job_stats
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error getting scheduler health: {str(e)}'
            }
    
    def get_job_status(self) -> Dict[str, Any]:
        """Get detailed job status information"""
        try:
            if not self.scheduler:
                return {
                    'status': 'not_initialized',
                    'message': 'Scheduler not initialized',
                    'jobs': []
                }
            
            jobs = self.scheduler.get_jobs()
            job_details = []
            
            for job in jobs:
                job_info = {
                    'id': job.id,
                    'name': job.name,
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger),
                    'func': job.func.__name__ if job.func else 'Unknown',
                    'args': job.args,
                    'kwargs': job.kwargs
                }
                job_details.append(job_info)
            
            return {
                'status': 'success',
                'total_jobs': len(job_details),
                'jobs': job_details,
                'job_stats': self.job_stats
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error getting job status: {str(e)}'
            }
    
    def trigger_manual_refresh(self, city_name: str, state: str = None, country: str = None) -> Dict[str, Any]:
        """Manually trigger hotel refresh for a specific city"""
        try:
            logger.info(f"Manual refresh triggered for {city_name}, {state}, {country}")
            
            # Get database session
            db = next(get_db())
            
            try:
                # Use the hotel refresh service for comprehensive data refresh
                refresh_result = self.hotel_refresh_service.refresh_hotels_for_city(
                    db, city_name, state, country
                )
                
                return {
                    'status': 'success',
                    'message': f'Manual refresh completed for {city_name}',
                    'result': refresh_result
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error in manual refresh for {city_name}: {str(e)}")
            return {
                'status': 'error',
                'message': f'Manual refresh failed: {str(e)}'
            }


# Global scheduler instance
scheduler_service = HotelSchedulerService()
