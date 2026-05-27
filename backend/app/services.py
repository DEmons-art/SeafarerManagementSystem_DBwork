from datetime import datetime

from .database import DatabaseIntegrityError, DbConnection
from .schemas import CrewCreate, CrewStatusUpdate, LoginRequest, VoyageCreate


# 多个查询共用的列清单，集中一处避免重复书写
CREW_FIELDS = "id, username, password, name, gender, id_card, phone, is_at_sea, role"
VOYAGE_FIELDS = (
    "record_id, crew_id, departure_point, destination_point, "
    "departure_time, expected_arrival_time, actual_arrival_time, status"
)


class ApiError(Exception):
    """业务异常：携带 HTTP 状态码与中文提示，由 main.py 统一转成 JSON。"""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message


def authenticate_user(db: DbConnection, payload: LoginRequest) -> dict:
    user = db.fetch_one(
        "SELECT id, username, password, name, role FROM crew_info "
        "WHERE username = %s AND password = %s",
        (payload.username, payload.password),
    )
    if user is None:
        raise ApiError(401, "账号或密码错误")
    return user


def list_crews(db: DbConnection) -> list[dict]:
    return db.fetch_all(f"SELECT {CREW_FIELDS} FROM crew_info ORDER BY id")


def get_crew(db: DbConnection, crew_id: int) -> dict:
    crew = db.fetch_one(
        f"SELECT {CREW_FIELDS} FROM crew_info WHERE id = %s", (crew_id,)
    )
    if crew is None:
        raise ApiError(404, "船员不存在")
    return crew


def create_crew(db: DbConnection, payload: CrewCreate) -> dict:
    try:
        crew_id = db.insert(
            """
            INSERT INTO crew_info (
                username, password, name, gender, id_card, phone, role, is_at_sea
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, 0)
            """,
            (
                payload.username,
                payload.password,
                payload.name,
                payload.gender,
                payload.id_card,
                payload.phone,
                payload.role,
            ),
        )
        db.commit()
    except DatabaseIntegrityError:
        db.rollback()
        raise ApiError(400, "账号或身份证号已被注册！")

    return get_crew(db, crew_id)


def delete_crew(db: DbConnection, crew_id: int) -> None:
    db.execute("DELETE FROM crew_info WHERE id = %s", (crew_id,))
    db.commit()


def update_crew_status(
    db: DbConnection,
    crew_id: int,
    payload: CrewStatusUpdate,
) -> dict:
    crew = db.fetch_one("SELECT id FROM crew_info WHERE id = %s", (crew_id,))
    if crew is None:
        raise ApiError(404, "船员不存在")

    db.execute(
        "UPDATE crew_info SET is_at_sea = %s WHERE id = %s",
        (payload.is_at_sea, crew_id),
    )
    if payload.is_at_sea == 0:
        db.execute(
            """
            UPDATE voyage_records
            SET status = %s, actual_arrival_time = %s
            WHERE crew_id = %s AND status = %s
            """,
            ("已抵达", datetime.now(), crew_id, "进行中"),
        )
    db.commit()
    return get_crew(db, crew_id)


def get_stats(db: DbConnection) -> dict[str, int]:
    row = db.fetch_one(
        "SELECT COUNT(id) AS total, COALESCE(SUM(is_at_sea), 0) AS at_sea FROM crew_info"
    )
    return {"total": int(row["total"]), "at_sea": int(row["at_sea"])}


def get_profile(db: DbConnection, crew_id: int) -> dict:
    crew = db.fetch_one(
        "SELECT id, username, name, gender, id_card, phone, is_at_sea "
        "FROM crew_info WHERE id = %s",
        (crew_id,),
    )
    if crew is None:
        raise ApiError(500, "获取个人资料失败")
    return crew


def list_voyages(db: DbConnection) -> list[dict]:
    return db.fetch_all(
        """
        SELECT
            v.record_id,
            v.crew_id,
            v.departure_point,
            v.destination_point,
            v.departure_time,
            v.expected_arrival_time,
            v.actual_arrival_time,
            v.status,
            c.name AS crew_name
        FROM voyage_records AS v
        JOIN crew_info AS c ON v.crew_id = c.id
        ORDER BY v.record_id DESC
        """
    )


def get_voyage(db: DbConnection, voyage_id: int) -> dict:
    voyage = db.fetch_one(
        f"SELECT {VOYAGE_FIELDS} FROM voyage_records WHERE record_id = %s",
        (voyage_id,),
    )
    if voyage is None:
        raise ApiError(500, "分配失败")
    return voyage


def create_voyage(db: DbConnection, payload: VoyageCreate) -> dict:
    crew = db.fetch_one(
        "SELECT id, is_at_sea FROM crew_info WHERE id = %s", (payload.crew_id,)
    )
    if crew is None:
        raise ApiError(400, "船员不存在")
    if crew["is_at_sea"] == 1:
        raise ApiError(400, "该船员正在出海中，无法重复派遣")

    try:
        voyage_id = db.insert(
            """
            INSERT INTO voyage_records (
                crew_id, departure_point, destination_point,
                departure_time, expected_arrival_time, status
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                payload.crew_id,
                payload.departure_point,
                payload.destination_point,
                payload.departure_time,
                payload.expected_arrival_time,
                "进行中",
            ),
        )
        db.execute(
            "UPDATE crew_info SET is_at_sea = 1 WHERE id = %s", (payload.crew_id,)
        )
        db.commit()
    except DatabaseIntegrityError:
        db.rollback()
        raise ApiError(500, "分配失败")

    return get_voyage(db, voyage_id)


def list_my_voyages(db: DbConnection, crew_id: int) -> list[dict]:
    return db.fetch_all(
        f"SELECT {VOYAGE_FIELDS} FROM voyage_records "
        "WHERE crew_id = %s ORDER BY record_id DESC",
        (crew_id,),
    )
