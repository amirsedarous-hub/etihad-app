from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class BuildingCreate(BaseModel):
    building_name: str
    building_type: Optional[str] = "عمارة"
    address: Optional[str] = None
    number_of_roles: Optional[str] = None

class BuildingOut(BuildingCreate):
    building_id: int
    class Config:
        orm_mode = True

class TreasuryCreate(BaseModel):
    treasury_name: str
    start_balance: Optional[float] = 0.0

class TreasuryOut(TreasuryCreate):
    treasury_id: int
    class Config:
        orm_mode = True

class OwnerCreate(BaseModel):
    owner_name: str
    owner_type: Optional[str] = "مالك"
    building_id: int
    flat_nu: str
    role: Optional[int] = None
    unit_type: Optional[int] = None
    area: Optional[float] = 0.0
    car_no: Optional[str] = None
    mobile: Optional[str] = None
    owner_ide: Optional[str] = None
    email: Optional[str] = None
    previous_debt: Optional[float] = 0.0

class OwnerOut(OwnerCreate):
    owner_id: int
    class Config:
        orm_mode = True

class CollectionTypeCreate(BaseModel):
    collection_type: str
    default_amount: Optional[float] = 0.0
    m_value: Optional[int] = 2
    allow_edit_amount: Optional[bool] = False

class CollectionGenerateRequest(BaseModel):
    building_id: int
    collection_type_id: int
    description: Optional[str] = None
    notes: Optional[str] = None

class ReceiptCreate(BaseModel):
    collection_detail_id: int
    treasury_id: int
    amount: float
    invoice_no: Optional[int] = None