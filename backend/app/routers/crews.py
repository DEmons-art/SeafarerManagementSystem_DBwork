from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import services
from ..dependencies import get_db, require_roles
from ..models import User
from ..schemas import CrewCreate, CrewUpdate


router = APIRouter(prefix="/api/crews", tags=["crews"])


@router.get("")
def list_crews(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("manager", "cert_admin", "shipowner", "admin")
    ),
):
    return {"success": True, "data": services.list_crews(db)}


@router.post("")
def create_crew(
    payload: CrewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("manager", "admin")),
):
    return {"success": True, "message": "船员录入成功", "data": services.create_crew(db, payload)}


@router.get("/{crew_id}")
def get_crew(
    crew_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("manager", "cert_admin", "shipowner", "admin")
    ),
):
    return {"success": True, "data": services.get_crew(db, crew_id)}


@router.put("/{crew_id}")
def update_crew(
    crew_id: int,
    payload: CrewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("manager", "admin")),
):
    return {
        "success": True,
        "message": "船员信息更新成功",
        "data": services.update_crew(db, crew_id, payload),
    }


@router.delete("/{crew_id}")
def delete_crew(
    crew_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("manager", "admin")),
):
    return {
        "success": True,
        "message": "船员已停用",
        "data": services.soft_delete_crew(db, crew_id),
    }
