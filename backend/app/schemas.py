from datetime import datetime
import re

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


PHONE_PATTERN = re.compile(r"^\+?\d{6,20}$")
ID_CARD_PATTERN = re.compile(r"^\d{15}$|^\d{17}[\dXx]$")


def _strip_text(value: str) -> str:
    return value.strip() if isinstance(value, str) else value


def _require_text(value: str, field_name: str, max_length: int | None = None) -> str:
    value = _strip_text(value)
    if not value:
        raise ValueError(f"{field_name}不能为空")
    if max_length is not None and len(value) > max_length:
        raise ValueError(f"{field_name}长度不能超过 {max_length} 个字符")
    return value


class LoginRequest(BaseModel):
    username: str
    password: str

    @field_validator("username", mode="before")
    @classmethod
    def validate_username(cls, value: str):
        return _require_text(value, "账号", 50)

    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, value: str):
        return _require_text(value, "密码")


class CrewCreate(BaseModel):
    username: str
    password: str
    name: str
    gender: str = "男"
    id_card: str
    phone: str | None = None
    role: str = "user"

    @field_validator("username", mode="before")
    @classmethod
    def validate_username(cls, value: str):
        return _require_text(value, "账号", 50)

    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, value: str):
        value = _require_text(value, "密码")
        if len(value) < 3:
            raise ValueError("密码长度不能少于 3 位")
        return value

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, value: str):
        return _require_text(value, "姓名", 50)

    @field_validator("gender", mode="before")
    @classmethod
    def validate_gender(cls, value: str):
        value = _strip_text(value)
        if value not in {"男", "女"}:
            raise ValueError("性别只能是男或女")
        return value

    @field_validator("id_card", mode="before")
    @classmethod
    def validate_id_card(cls, value: str):
        value = _require_text(value, "身份证号", 18)
        if not ID_CARD_PATTERN.fullmatch(value):
            raise ValueError("身份证号格式不正确")
        return value

    @field_validator("phone", mode="before")
    @classmethod
    def validate_phone(cls, value: str | None):
        value = _strip_text(value)
        if value in (None, ""):
            return None
        if not PHONE_PATTERN.fullmatch(value):
            raise ValueError("联系电话格式不正确")
        return value

    @field_validator("role", mode="before")
    @classmethod
    def validate_role(cls, value: str):
        value = _strip_text(value)
        if value not in {"user", "admin"}:
            raise ValueError("系统角色只能是 user 或 admin")
        return value


class CrewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    password: str
    name: str
    gender: str
    id_card: str
    phone: str | None
    is_at_sea: int
    role: str


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    name: str
    gender: str
    id_card: str
    phone: str | None
    is_at_sea: int


class CrewStatusUpdate(BaseModel):
    is_at_sea: int

    @field_validator("is_at_sea")
    @classmethod
    def validate_status(cls, value: int):
        if value not in {0, 1}:
            raise ValueError("出海状态只能是 0 或 1")
        return value


class VoyageCreate(BaseModel):
    crew_id: int
    departure_point: str
    destination_point: str
    departure_time: datetime
    expected_arrival_time: datetime

    @field_validator("departure_point", "destination_point", mode="before")
    @classmethod
    def validate_port(cls, value: str, info):
        value = _strip_text(value)
        if not value:
            field_name = "出发港口" if info.field_name == "departure_point" else "目的港口"
            raise ValueError(f"{field_name}不能为空")
        return value

    @model_validator(mode="after")
    def validate_time_order(self):
        if self.expected_arrival_time < self.departure_time:
            raise ValueError("预计到达时间不能早于出发时间")
        return self


class VoyageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    record_id: int
    crew_id: int
    departure_point: str
    destination_point: str
    departure_time: datetime
    expected_arrival_time: datetime
    actual_arrival_time: datetime | None
    status: str
