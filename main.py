from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from database import SessionLocal, engine, Base
from models import Product, User

# Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# create tables if not exist
Base.metadata.create_all(bind=engine)

app = FastAPI()
# session middleware (change secret in production)
app.add_middleware(SessionMiddleware, secret_key="change-me-please")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# DB dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ----------------- helpers -----------------
def current_user(request: Request):
    return request.session.get("user")


# ----------------- Routes -----------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "products": products, "user": current_user(request)}
    )


@app.get("/product/{product_id}", response_class=HTMLResponse)
def product_detail(request: Request, product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(
        "product_detail.html",
        {"request": request, "product": product, "user": current_user(request)}
    )


@app.post("/add_to_cart/{product_id}")
def add_to_cart(product_id: int, request: Request, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return RedirectResponse(url="/", status_code=303)
    cart = request.session.get("cart", {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    request.session["cart"] = cart
    # redirect back to product or cart — here we send to cart
    return RedirectResponse(url="/cart", status_code=303)


@app.post("/remove_from_cart/{product_id}")
def remove_from_cart(product_id: int, request: Request):
    cart = request.session.get("cart", {})
    key = str(product_id)
    if key in cart:
        cart[key] -= 1
        if cart[key] <= 0:
            del cart[key]
    request.session["cart"] = cart
    return RedirectResponse(url="/cart", status_code=303)


@app.get("/cart", response_class=HTMLResponse)
def view_cart(request: Request, db: Session = Depends(get_db)):
    cart = request.session.get("cart", {})
    product_ids = [int(pid) for pid in cart.keys()] if cart else []
    products = db.query(Product).filter(Product.id.in_(product_ids)).all() if product_ids else []
    cart_items = []
    total = 0.0
    for p in products:
        qty = cart.get(str(p.id), 0)
        subtotal = p.price * qty
        total += subtotal
        cart_items.append({"product": p, "qty": qty, "subtotal": subtotal})
    return templates.TemplateResponse(
        "cart.html",
        {"request": request, "cart_items": cart_items, "total": total, "user": current_user(request)}
    )


@app.get("/checkout", response_class=HTMLResponse)
def checkout_page(request: Request):
    user = current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    cart = request.session.get("cart", {})
    if not cart:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(
        "checkout.html",
        {"request": request, "user": user}
    )


@app.post("/place_order")
def place_order(request: Request,
                name: str = Form(...),
                address: str = Form(...),
                payment: str = Form(...)):
    user = current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    # simulate order placement
    request.session.pop("cart", None)
    return templates.TemplateResponse(
        "order_success.html",
        {"request": request, "name": name, "payment": payment, "user": user}
    )


# ------- auth -------
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "user": current_user(request)})


@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not pwd_context.verify(password, user.hashed_password):
        # simple failure handling: redirect back to login (could show message)
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials", "user": None})
    # set session
    request.session["user"] = user.username
    return RedirectResponse(url="/", status_code=303)


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "user": current_user(request)})


@app.post("/register")
def register(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Username taken", "user": None})
    user = User(username=username, hashed_password=pwd_context.hash(password))
    db.add(user)
    db.commit()
    request.session["user"] = user.username
    return RedirectResponse(url="/", status_code=303)


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)
