# seed.py
from database import Base, engine, SessionLocal
from models import Product, User
from passlib.context import CryptContext

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ensure tables exist (will create fresh tables in new ecommerce.db)
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# optional: clear existing content (safe if db was recreated)
try:
    db.query(Product).delete()
    db.query(User).delete()
    db.commit()
except Exception:
    db.rollback()

items = [
    Product(
        name="Laptop",
        price=750.00,
        description="High performance laptop for developers and gamers.",
        image_url="https://via.placeholder.com/400x300?text=Laptop"
    ),
    Product(
        name="Smartphone",
        price=400.00,
        description="Latest smartphone with excellent camera & battery life.",
        image_url="https://via.placeholder.com/400x300?text=Smartphone"
    ),
    Product(
        name="Headphones",
        price=50.00,
        description="Noise cancelling over-ear headphones.",
        image_url="https://via.placeholder.com/400x300?text=Headphones"
    ),
    Product(
        name="Keyboard",
        price=30.00,
        description="Mechanical keyboard with RGB backlight.",
        image_url="https://via.placeholder.com/400x300?text=Keyboard"
    ),
]

db.add_all(items)

# create demo user (username: demo password: demo123)
demo = User(username="demo", hashed_password=pwd.hash("demo123"))
db.add(demo)

db.commit()
db.close()

print("✅ Database seeded with products and demo user (demo / demo123)")
