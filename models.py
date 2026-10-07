from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, 
    DateTime, ForeignKey, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship
from database import Base

class Setting(Base):
    __tablename__ = "setting"
    id = Column(Integer, primary_key=True, index=True)
    barcode_printer = Column(String(255), nullable=True)
    report_printer = Column(String(255), nullable=True)
    receipt_printer = Column(String(255), nullable=True)
    previewer_page = Column(Boolean, default=False)
    paper_a4 = Column(Boolean, default=False)
    mobile = Column(String(20), nullable=True)
    pro_owner = Column(String(255), nullable=True)

class Building(Base):
    __tablename__ = "tbl_building"
    building_id = Column(Integer, primary_key=True, index=True)
    building_name = Column(String(255), nullable=False)
    building_type = Column(String(50), default="عمارة")
    distribution_ratio = Column(Float, default=0.0)
    address = Column(String(255), nullable=True)
    number_of_roles = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)

    owners = relationship("Owner", back_populates="building")
    expenses = relationship("Expense", back_populates="building")
    collections = relationship("Collection", back_populates="building")

class Role(Base):
    __tablename__ = "tbl_role"
    role_id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String(100), nullable=False)

    owners = relationship("Owner", back_populates="role_rel")

class UnitType(Base):
    __tablename__ = "tbl_unite_type"
    unit_type_id = Column(Integer, primary_key=True, index=True)
    unit_type = Column(String(100), nullable=False)
    building_type = Column(String(50), default="عمارة")
    factor = Column(Float, default=1.0)

    owners = relationship("Owner", back_populates="unit_type_rel")
    pricing_details = relationship("CollectionTypeDetail", back_populates="unit_type_rel")

class Owner(Base):
    __tablename__ = "tbl_owner"
    owner_id = Column(Integer, primary_key=True, index=True)
    owner_name = Column(String(255), nullable=False)
    owner_type = Column(String(50), default="مالك")
    building_id = Column(Integer, ForeignKey("tbl_building.building_id"))
    flat_nu = Column(String(50), nullable=False)
    role = Column(Integer, ForeignKey("tbl_role.role_id"), nullable=True)
    unit_type = Column(Integer, ForeignKey("tbl_unite_type.unit_type_id"), nullable=True)
    area = Column(Float, default=0.0)
    car_no = Column(String(50), nullable=True)
    mobile = Column(String(50), nullable=True)
    owner_ide = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)
    previous_debt = Column(Float, default=0.0)
    date_debt = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    building = relationship("Building", back_populates="owners")
    role_rel = relationship("Role", back_populates="owners")
    unit_type_rel = relationship("UnitType", back_populates="owners")
    collection_details = relationship("CollectionDetail", back_populates="owner_rel")

class Treasury(Base):
    __tablename__ = "tbl_treasury"
    treasury_id = Column(Integer, primary_key=True, index=True)
    treasury_name = Column(String(255), nullable=False, unique=True)
    start_balance = Column(Float, default=0.0)
    is_default = Column(Boolean, default=False)
    description = Column(String(255), nullable=True)

class CollectionType(Base):
    __tablename__ = "tbl_collection_type"
    collection_type_id = Column(Integer, primary_key=True, index=True)
    collection_type = Column(String(255), nullable=False)
    finished = Column(Boolean, default=False)
    m_value = Column(Integer, default=2) # 1 = بالمتر، 2 = قيمة ثابتة
    default_amount = Column(Float, default=0.0)
    allow_edit_amount = Column(Boolean, default=False)

    details_pricing = relationship("CollectionTypeDetail", back_populates="col_type_rel")

class CollectionTypeDetail(Base):
    __tablename__ = "tbl_details_collection_type"
    id = Column(Integer, primary_key=True, index=True)
    collection_type_id = Column(Integer, ForeignKey("tbl_collection_type.collection_type_id"))
    unit_type_id = Column(Integer, ForeignKey("tbl_unite_type.unit_type_id"))
    amount = Column(Float, default=0.0)

    col_type_rel = relationship("CollectionType", back_populates="details_pricing")
    unit_type_rel = relationship("UnitType", back_populates="pricing_details")
    __table_args__ = (UniqueConstraint('collection_type_id', 'unit_type_id', name='uq_col_unit_type'),)

class Collection(Base):
    __tablename__ = "tbl_collection"
    collection_id = Column(Integer, primary_key=True, index=True)
    building_id = Column(Integer, ForeignKey("tbl_building.building_id"))
    collection_type_id = Column(Integer, ForeignKey("tbl_collection_type.collection_type_id"))
    date_ = Column(DateTime, default=datetime.utcnow)
    description = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    building = relationship("Building", back_populates="collections")
    items = relationship("CollectionDetail", back_populates="parent_collection")

class CollectionDetail(Base):
    __tablename__ = "tbl_collection_details"
    id = Column(Integer, primary_key=True, index=True)
    collection_id = Column(Integer, ForeignKey("tbl_collection.collection_id"))
    owner_id = Column(Integer, ForeignKey("tbl_owner.owner_id"))
    amount = Column(Float, default=0.0)
    paid = Column(Float, default=0.0)
    rest = Column(Float, default=0.0)
    paid_ok = Column(Boolean, default=False)
    date_ = Column(DateTime, default=datetime.utcnow)

    parent_collection = relationship("Collection", back_populates="items")
    owner_rel = relationship("Owner", back_populates="collection_details")
    receipts = relationship("CollectionSubDetail", back_populates="detail_rel")
    __table_args__ = (UniqueConstraint('collection_id', 'owner_id', name='uq_col_owner'),)

class CollectionSubDetail(Base):
    __tablename__ = "tbl_collection_sub_details"
    id = Column(Integer, primary_key=True, index=True)
    collection_id_details = Column(Integer, ForeignKey("tbl_collection_details.id"))
    invoice_no = Column(Integer, index=True)
    amount = Column(Float, nullable=False)
    treasury_id = Column(Integer, ForeignKey("tbl_treasury.treasury_id"))
    date_ = Column(DateTime, default=datetime.utcnow)

    detail_rel = relationship("CollectionDetail", back_populates="receipts")

class ExpenseType(Base):
    __tablename__ = "tbl_expenses_type"
    expenses_type_id = Column(Integer, primary_key=True, index=True)
    expenses_type = Column(String(255), nullable=False, unique=True)

class Expense(Base):
    __tablename__ = "tbl_expenses"
    expenses_id = Column(Integer, primary_key=True, index=True)
    date_ = Column(DateTime, default=datetime.utcnow)
    treasury_id = Column(Integer, ForeignKey("tbl_treasury.treasury_id"))
    expenses_type_id = Column(Integer, ForeignKey("tbl_expenses_type.expenses_type_id"))
    building_id = Column(Integer, ForeignKey("tbl_building.building_id"))
    amount = Column(Float, nullable=False)
    description = Column(String(255), nullable=True)

    building = relationship("Building", back_populates="expenses")

class RevenueType(Base):
    __tablename__ = "tbl_revenue_type"
    revenue_type_id = Column(Integer, primary_key=True, index=True)
    revenue_type = Column(String(255), nullable=False, unique=True)

class Revenue(Base):
    __tablename__ = "tbl_revenue"
    revenue_id = Column(Integer, primary_key=True, index=True)
    date_ = Column(DateTime, default=datetime.utcnow)
    treasury_id = Column(Integer, ForeignKey("tbl_treasury.treasury_id"))
    revenue_type_id = Column(Integer, ForeignKey("tbl_revenue_type.revenue_type_id"))
    building_id = Column(Integer, ForeignKey("tbl_building.building_id"))
    amount = Column(Float, nullable=False)
    description = Column(String(255), nullable=True)

class DepositType(Base):
    __tablename__ = "tbl_deposit_type"
    deposit_type_id = Column(Integer, primary_key=True, index=True)
    deposit_type = Column(String(255), nullable=False, unique=True)

class Deposit(Base):
    __tablename__ = "tbl_deposit"
    deposit_id = Column(Integer, primary_key=True, index=True)
    deposit_type_id = Column(Integer, ForeignKey("tbl_deposit_type.deposit_type_id"))
    amount = Column(Float, default=0.0)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    treasury_id = Column(Integer, ForeignKey("tbl_treasury.treasury_id"))
    interest_value = Column(Float, default=0.0)
    deposit_expires = Column(Boolean, default=False)

    interests = relationship("DepositInterest", back_populates="deposit_rel")

class DepositInterest(Base):
    __tablename__ = "tbl_interests"
    interest_id = Column(Integer, primary_key=True, index=True)
    deposit_id = Column(Integer, ForeignKey("tbl_deposit.deposit_id"))
    interest_date = Column(DateTime, nullable=False)
    interest_value = Column(Float, default=0.0)
    treasury_id = Column(Integer, ForeignKey("tbl_treasury.treasury_id"))

    deposit_rel = relationship("Deposit", back_populates="interests")

class TransferMoney(Base):
    __tablename__ = "tbl_transfer_money"
    transfer_money_id = Column(Integer, primary_key=True, index=True)
    date_ = Column(DateTime, default=datetime.utcnow)
    treasury_from = Column(Integer, ForeignKey("tbl_treasury.treasury_id"))
    treasury_to = Column(Integer, ForeignKey("tbl_treasury.treasury_id"))
    amount = Column(Float, nullable=False)
    description = Column(String(255), nullable=True)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String(100), nullable=False)
    username = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)

    permissions = relationship("UserPermission", back_populates="user_rel")

class UserPermission(Base):
    __tablename__ = "user_permission"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    form_name = Column(String(100), nullable=False)
    form_title = Column(String(100), nullable=True)
    allow_view = Column(Boolean, default=False)
    allow_add = Column(Boolean, default=False)
    allow_modify = Column(Boolean, default=False)
    allow_delete = Column(Boolean, default=False)
    full_control = Column(Boolean, default=False)

    user_rel = relationship("User", back_populates="permissions")
    __table_args__ = (UniqueConstraint('user_id', 'form_name', name='uq_user_form'),)