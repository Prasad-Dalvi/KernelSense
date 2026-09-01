from fastapi import APIRouter, Query

from database.database import (
    get_command_history,
    get_health_history
)

router = APIRouter()


@router.get("/history/commands")
def command_history(
    limit: int = Query(default=50, ge=1, le=100)
):
    return {
        "success": True,
        "data": get_command_history(limit)
    }


@router.get("/history/health")
def health_history(
    limit: int = Query(default=50, ge=1, le=100)
):
    return {
        "success": True,
        "data": get_health_history(limit)
    }
