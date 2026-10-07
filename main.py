from datetime import datetime
from typing import List
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

import models
import schemas
from database import get_db


# إنشاء الجداول آلياً إذا لم تكن موجودة
# models.Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="نظام إدارة اتحاد الشاغلين (AccessPro Web)",
    description="Backend API لنظام إدارة العقارات والماليات",
    version="2.0.0"
)

templates = Jinja2Templates(directory="templates")

# ==========================================
# 1. الواجهات (UI Views)
# ==========================================

@app.get("/", response_class=HTMLResponse, tags=["الواجهة"])
def render_dashboard(request: Request, db: Session = Depends(get_db)):
    buildings = db.query(models.Building).all()
    treasuries = db.query(models.Treasury).all()
    owners = db.query(models.Owner).all()
    
    # جلب البيانات للحساب بأمان داخل بايثون لتفادي تعليق SQLite
    sub_details = db.query(models.CollectionSubDetail).all()
    expenses = db.query(models.Expense).all()
    revenues = db.query(models.Revenue).all()
    collection_items = db.query(models.CollectionDetail).all()
    
    current_month_str = datetime.now().strftime('%Y-%m')
    
    # مجموع سندات القبض لهذا الشهر
    month_collections = sum(
        (s.amount or 0.0) for s in sub_details 
        if s.date_ and s.date_.strftime('%Y-%m') == current_month_str
    )
    
    # مجموع المصروفات لهذا الشهر
    month_expenses = sum(
        (e.amount or 0.0) for e in expenses 
        if e.date_ and e.date_.strftime('%Y-%m') == current_month_str
    )
    
    # مجموع الإيرادات لهذا الشهر
    month_revenues = sum(
        (r.amount or 0.0) for r in revenues 
        if r.date_ and r.date_.strftime('%Y-%m') == current_month_str
    )
    
    # رصيد الخزائن الكلي
    total_balance = sum((t.start_balance or 0.0) for t in treasuries)
    
    # إجمالي المتأخرات والمديونية
    total_rest = sum((c.rest or 0.0) for c in collection_items)
    total_prev = sum((o.previous_debt or 0.0) for o in owners)
    grand_debt = total_rest + total_prev

    context = {
        "request": request,
        "buildings": buildings,
        "treasuries": treasuries,
        "owners_count": len(owners),
        "total_balance": f"{total_balance:,.2f}",
        "month_collections": f"{month_collections:,.2f}",
        "month_expenses": f"{month_expenses:,.2f}",
        "month_revenues": f"{month_revenues:,.2f}",
        "grand_debt": f"{grand_debt:,.2f}"
    }
    return templates.TemplateResponse(request=request, name="dashboard.html", context=context)


@app.get("/owners-page", response_class=HTMLResponse, tags=["الواجهة"])
def render_owners_page(request: Request, db: Session = Depends(get_db)):
    owners = db.query(models.Owner).all()
    buildings = db.query(models.Building).all()
    roles = db.query(models.Role).all()
    unit_types = db.query(models.UnitType).all()

    context = {
        "request": request,
        "owners": owners,
        "buildings": buildings,
        "roles": roles,
        "unit_types": unit_types
    }
    return templates.TemplateResponse(request=request, name="owners.html", context=context)


@app.get("/collections-page", response_class=HTMLResponse, tags=["الواجهة"])
def render_collections_page(request: Request, db: Session = Depends(get_db)):
    # التأكد من وجود بند تحصيل افتراضي إن كان الجدول فارغاً
    if db.query(models.CollectionType).count() == 0:
        default_type = models.CollectionType(
            collection_type="صيانة شهرية",
            default_amount=300.0,
            m_value=2,
            finished=False
        )
        db.add(default_type)
        db.commit()

    collections = db.query(models.Collection).order_by(models.Collection.collection_id.desc()).all()
    buildings = db.query(models.Building).all()
    col_types = db.query(models.CollectionType).filter(models.CollectionType.finished == False).all()
    treasuries = db.query(models.Treasury).all()
    roles = db.query(models.Role).all()

    context = {
        "request": request,
        "collections": collections,
        "buildings": buildings,
        "col_types": col_types,
        "treasuries": treasuries,
        "roles": roles
    }
    return templates.TemplateResponse(request=request, name="collections.html", context=context)


# ==========================================
# 2. مسارات العقارات والخزائن
# ==========================================

@app.post("/buildings", tags=["العقارات"])
def add_building(payload: schemas.BuildingCreate, db: Session = Depends(get_db)):
    b = models.Building(**payload.dict())
    db.add(b)
    db.commit()
    db.refresh(b)
    return b

@app.post("/treasuries", tags=["الخزائن"])
def add_treasury(payload: schemas.TreasuryCreate, db: Session = Depends(get_db)):
    t = models.Treasury(**payload.dict())
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


# ==========================================
# 3. مسارات الشاغلين (CRUD)
# ==========================================

@app.post("/owners", tags=["الشاغلين"])
def add_owner(payload: schemas.OwnerCreate, db: Session = Depends(get_db)):
    owner = models.Owner(**payload.dict())
    db.add(owner)
    db.commit()
    db.refresh(owner)
    return owner

@app.delete("/owners/{owner_id}", tags=["الشاغلين"])
def delete_owner(owner_id: int, db: Session = Depends(get_db)):
    owner = db.query(models.Owner).filter(models.Owner.owner_id == owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="الشاغل غير موجود")
    db.delete(owner)
    db.commit()
    return {"status": "deleted"}


# ==========================================
# 4. مسارات الالتزامات والتحصيل (Collections)
# ==========================================

@app.get("/collection-items/{collection_id}", tags=["التحصيلات"])
def get_collection_items(collection_id: int, db: Session = Depends(get_db)):
    """جلب تفاصيل ومطالبات الوحدات لالتزام محدد مع حالة السداد"""
    items = db.query(models.CollectionDetail).filter(
        models.CollectionDetail.collection_id == collection_id
    ).all()
    
    result = []
    for it in items:
        owner = it.owner_rel
        result.append({
            "id": it.id,
            "owner_id": it.owner_id,
            "owner_name": owner.owner_name if owner else "—",
            "flat_nu": owner.flat_nu if owner else "—",
            "role_name": owner.role_rel.role_name if owner and owner.role_rel else "—",
            "amount": it.amount,
            "paid": it.paid,
            "rest": it.rest,
            "paid_ok": it.paid_ok
        })
    return result


@app.post("/collections/generate", tags=["التحصيلات"])
def generate_collection(payload: schemas.CollectionGenerateRequest, db: Session = Depends(get_db)):
    """توليد التزام ومطالبات لكافة وحدات العقار آلياً"""
    col_type = db.query(models.CollectionType).filter(
        models.CollectionType.collection_type_id == payload.collection_type_id
    ).first()
    if not col_type:
        raise HTTPException(status_code=404, detail="نوع التحصيل غير موجود")

    col_head = models.Collection(
        building_id=payload.building_id,
        collection_type_id=payload.collection_type_id,
        description=payload.description,
        notes=payload.notes,
        date_=datetime.now()
    )
    db.add(col_head)
    db.flush()

    owners = db.query(models.Owner).filter(models.Owner.building_id == payload.building_id).all()
    if not owners:
        raise HTTPException(status_code=400, detail="لا توجد وحدات مسجلة في هذا العقار")

    custom_prices = {
        p.unit_type_id: p.amount 
        for p in col_type.details_pricing
    }

    for o in owners:
        if o.unit_type in custom_prices:
            req_amount = custom_prices[o.unit_type]
        elif col_type.m_value == 1:
            req_amount = (o.area or 0.0) * (col_type.default_amount or 0.0)
        else:
            req_amount = col_type.default_amount or 0.0

        detail = models.CollectionDetail(
            collection_id=col_head.collection_id,
            owner_id=o.owner_id,
            amount=req_amount,
            paid=0.0,
            rest=req_amount,
            paid_ok=(req_amount == 0.0),
            date_=datetime.now()
        )
        db.add(detail)

    db.commit()
    return {"status": "success", "collection_id": col_head.collection_id}


@app.post("/collections/pay-full/{detail_id}", tags=["التحصيلات"])
def pay_full(detail_id: int, treasury_id: int = 1, db: Session = Depends(get_db)):
    """سداد المبلغ بالكامل لوحدة محددة"""
    item = db.query(models.CollectionDetail).filter(models.CollectionDetail.id == detail_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="المطالبة غير موجودة")
    
    remaining = item.rest
    if remaining <= 0:
        return {"status": "already_paid"}

    last_inv = db.query(func.max(models.CollectionSubDetail.invoice_no)).scalar() or 100
    new_inv = last_inv + 1

    sub = models.CollectionSubDetail(
        collection_id_details=item.id,
        invoice_no=new_inv,
        amount=remaining,
        treasury_id=treasury_id,
        date_=datetime.now()
    )
    db.add(sub)

    item.paid += remaining
    item.rest = 0.0
    item.paid_ok = True
    db.commit()

    return {"status": "success", "invoice_no": new_inv}


@app.post("/collections/pay-all-units/{collection_id}", tags=["التحصيلات"])
def pay_all_units(collection_id: int, treasury_id: int = 1, db: Session = Depends(get_db)):
    """سداد كامل المطالبات لجميع الوحدات بضغطة زر واحدة"""
    items = db.query(models.CollectionDetail).filter(
        models.CollectionDetail.collection_id == collection_id,
        models.CollectionDetail.paid_ok == False
    ).all()

    last_inv = db.query(func.max(models.CollectionSubDetail.invoice_no)).scalar() or 100

    for item in items:
        rem = item.rest
        if rem > 0:
            last_inv += 1
            sub = models.CollectionSubDetail(
                collection_id_details=item.id,
                invoice_no=last_inv,
                amount=rem,
                treasury_id=treasury_id,
                date_=datetime.now()
            )
            db.add(sub)
            item.paid += rem
            item.rest = 0.0
            item.paid_ok = True

    db.commit()
    return {"status": "success"}