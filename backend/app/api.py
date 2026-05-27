from fastapi import APIRouter, Depends, Request

from . import services
from .database import Database, DbConnection
from .schemas import (
    CrewCreate,
    CrewOut,
    CrewStatusUpdate,
    LoginRequest,
    ProfileOut,
    VoyageCreate,
    VoyageOut,
)


router = APIRouter()


def get_db(request: Request):
    database: Database = request.app.state.database
    db = database.connect()
    try:
        yield db
    finally:
        db.close()


@router.get("/health")
def health():
    return {"success": True, "message": "FastAPI backend is running"}


@router.post("/api/login")
def login(payload: LoginRequest, db: DbConnection = Depends(get_db)):
    user = services.authenticate_user(db, payload)
    return {
        "success": True,
        "message": "登录成功",
        "role": user["role"],
        "name": user["name"],
        "id": user["id"],
    }


@router.get("/api/crews")
def list_crews(db: DbConnection = Depends(get_db)):
    crews = services.list_crews(db)
    return {"success": True, "data": [CrewOut.model_validate(crew) for crew in crews]}


@router.post("/api/crews")
def create_crew(payload: CrewCreate, db: DbConnection = Depends(get_db)):
    crew = services.create_crew(db, payload)
    return {
        "success": True,
        "message": "船员录入成功！",
        "data": CrewOut.model_validate(crew),
    }


@router.delete("/api/crews/{crew_id}")
def delete_crew(crew_id: int, db: DbConnection = Depends(get_db)):
    services.delete_crew(db, crew_id)
    return {"success": True, "message": "船员已移出系统！"}


@router.put("/api/crews/{crew_id}/status")
def update_crew_status(
    crew_id: int,
    payload: CrewStatusUpdate,
    db: DbConnection = Depends(get_db),
):
    crew = services.update_crew_status(db, crew_id, payload)
    return {
        "success": True,
        "message": "状态更新成功！",
        "data": CrewOut.model_validate(crew),
    }


@router.get("/api/stats")
def stats(db: DbConnection = Depends(get_db)):
    return {"success": True, "data": services.get_stats(db)}


@router.get("/api/voyages")
def list_voyages(db: DbConnection = Depends(get_db)):
    data = []
    for voyage in services.list_voyages(db):
        item = VoyageOut.model_validate(voyage).model_dump()
        item["crew_name"] = voyage["crew_name"]
        data.append(item)
    return {"success": True, "data": data}


@router.post("/api/voyages")
def create_voyage(payload: VoyageCreate, db: DbConnection = Depends(get_db)):
    voyage = services.create_voyage(db, payload)
    return {
        "success": True,
        "message": "航次任务分配成功！",
        "data": VoyageOut.model_validate(voyage),
    }


@router.get("/api/my-profile/{crew_id}")
def my_profile(crew_id: int, db: DbConnection = Depends(get_db)):
    crew = services.get_profile(db, crew_id)
    return {"success": True, "data": ProfileOut.model_validate(crew)}


@router.get("/api/my-voyages/{crew_id}")
def my_voyages(crew_id: int, db: DbConnection = Depends(get_db)):
    voyages = services.list_my_voyages(db, crew_id)
    return {
        "success": True,
        "data": [VoyageOut.model_validate(voyage) for voyage in voyages],
    }
