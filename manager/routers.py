from fastapi import APIRouter

from activities.endpoints import router as activity_router
from buildings.endpoints import router as building_router
from organizations.endpoints import router as organization_router

main_router = APIRouter(prefix="/api")
main_router.include_router(building_router)
main_router.include_router(activity_router)
main_router.include_router(organization_router)
