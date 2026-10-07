from database import engine, Base, SessionLocal
import models

def init_db():
    print("جاري إنشاء الجداول...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    # إضافة الأدوار الأساسية إن لم تكن موجودة
    if db.query(models.Role).count() == 0:
        roles = ["الأرضي", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس", "السابع", "الثامن", "التاسع", "العاشر"]
        for r in roles:
            db.add(models.Role(role_name=r))
            
    # إضافة أنواع الوحدات الأساسية
    if db.query(models.UnitType).count() == 0:
        types = [
            ("سكني", 1.0),
            ("تجاري", 1.2),
            ("مغلقة", 0.6),
            ("بدون أسانسير", 0.5)
        ]
        for name, factor in types:
            db.add(models.UnitType(unit_type=name, factor=factor))
            
    # إضافة خزينة افتراضية
    if db.query(models.Treasury).count() == 0:
        db.add(models.Treasury(treasury_name="الخزينة الرئيسية", start_balance=0.0, is_default=True))
        db.add(models.Treasury(treasury_name="بنك CIB", start_balance=0.0, is_default=False))
        
    db.commit()
    db.close()
    print("تم إعداد الجداول والبيانات الافتراضية بنجاح!")

if __name__ == "__main__":
    init_db()