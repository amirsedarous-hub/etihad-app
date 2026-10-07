import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# تحميل الرابط من ملف .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ خطأ: لم يتم العثور على DATABASE_URL في ملف .env")
    exit(1)

# توافق رابط الاتصال مع SQLAlchemy
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

try:
    # الاتصال بقاعدة البيانات في Neon
    engine = create_engine(DATABASE_URL)
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version();"))
        print("\n✅ تم الاتصال بقاعدة بيانات Neon السحابية بنجاح!")
        print(f"بيانات الخادم:\n{result.scalar()}\n")
except Exception as e:
    print("\n❌ فشل الاتصال، تفاصيل الخطأ:")
    print(e)