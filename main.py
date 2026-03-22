from fastapi import FastAPI, HTTPException, Query, Response
from pydantic import BaseModel, Field
from typing import Optional
import math

app = FastAPI()

# -----------------------------
# Q1 Home
# -----------------------------
@app.get("/")
def home():
    return {"message": "Welcome to QuickBite Food Delivery"}

# -----------------------------
# Q2 Menu Data
# -----------------------------
menu = [
    {"id": 1, "name": "Margherita Pizza", "price": 200, "category": "Pizza", "is_available": True},
    {"id": 2, "name": "Veg Burger", "price": 120, "category": "Burger", "is_available": True},
    {"id": 3, "name": "Coke", "price": 50, "category": "Drink", "is_available": True},
    {"id": 4, "name": "Chocolate Cake", "price": 150, "category": "Dessert", "is_available": False},
    {"id": 5, "name": "Chicken Pizza", "price": 300, "category": "Pizza", "is_available": True},
    {"id": 6, "name": "Ice Cream", "price": 90, "category": "Dessert", "is_available": True},
]

# -----------------------------
# Q4 Orders
# -----------------------------
orders = []
order_counter = 1

# -----------------------------
# Q3 & Q5 (ORDER MATTERS)
# -----------------------------
@app.get("/menu/summary")
def menu_summary():
    total = len(menu)
    available = len([i for i in menu if i["is_available"]])
    unavailable = total - available
    categories = list(set(i["category"] for i in menu))
    return {
        "total_items": total,
        "available": available,
        "unavailable": unavailable,
        "categories": categories
    }

@app.get("/menu")
def get_menu():
    return {"items": menu, "total": len(menu)}

@app.get("/menu/{item_id}")
def get_item(item_id: int):
    for item in menu:
        if item["id"] == item_id:
            return item
    return {"error": "Item not found"}

@app.get("/orders")
def get_orders():
    return {"orders": orders, "total_orders": len(orders)}

# -----------------------------
# Q6 Model
# -----------------------------
class OrderRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    item_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=20)
    delivery_address: str = Field(..., min_length=10)
    order_type: str = "delivery"

# -----------------------------
# Q7 Helpers
# -----------------------------
def find_menu_item(item_id: int):
    for item in menu:
        if item["id"] == item_id:
            return item
    return None

def calculate_bill(price, quantity, order_type="delivery"):
    total = price * quantity
    if order_type == "delivery":
        total += 30
    return total

# -----------------------------
# Q8 & Q9 POST Order
# -----------------------------
@app.post("/orders")
def create_order(order: OrderRequest):
    global order_counter

    item = find_menu_item(order.item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if not item["is_available"]:
        raise HTTPException(status_code=400, detail="Item not available")

    total = calculate_bill(item["price"], order.quantity, order.order_type)

    new_order = {
        "order_id": order_counter,
        "customer_name": order.customer_name,
        "item": item["name"],
        "quantity": order.quantity,
        "total_price": total,
        "type": order.order_type
    }

    orders.append(new_order)
    order_counter += 1

    return new_order

# -----------------------------
# Q10 Filter
# -----------------------------
@app.get("/menu-filter")
def filter_menu(
    category: Optional[str] = None,
    max_price: Optional[int] = None,
    is_available: Optional[bool] = None
):
    results = menu

    if category is not None:
        results = [i for i in results if i["category"].lower() == category.lower()]

    if max_price is not None:
        results = [i for i in results if i["price"] <= max_price]

    if is_available is not None:
        results = [i for i in results if i["is_available"] == is_available]

    return {"items": results, "count": len(results)}

# -----------------------------
# Q11 Add Menu Item
# -----------------------------
class NewMenuItem(BaseModel):
    name: str = Field(..., min_length=2)
    price: float = Field(..., gt=0)
    category: str = Field(..., min_length=2)
    is_available: bool = True

@app.post("/menu", status_code=201)
def add_menu_item(item: NewMenuItem):
    for m in menu:
        if m["name"].lower() == item.name.lower():
            raise HTTPException(status_code=400, detail="Duplicate item")

    new_item = item.dict()
    new_item["id"] = len(menu) + 1
    menu.append(new_item)
    return new_item

# -----------------------------
# Q12 Update
# -----------------------------
@app.put("/menu/{item_id}")
def update_menu(
    item_id: int,
    price: Optional[int] = None,
    is_available: Optional[bool] = None
):
    item = find_menu_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if price is not None:
        item["price"] = price

    if is_available is not None:
        item["is_available"] = is_available

    return item

# -----------------------------
# Q13 Delete
# -----------------------------
@app.delete("/menu/{item_id}")
def delete_item(item_id: int):
    item = find_menu_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    menu.remove(item)
    return {"message": f"{item['name']} deleted"}

# -----------------------------
# Q14 Cart
# -----------------------------
cart = []

@app.post("/cart/add")
def add_to_cart(item_id: int, quantity: int = 1):
    item = find_menu_item(item_id)

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if not item["is_available"]:
        raise HTTPException(status_code=400, detail="Item unavailable")

    for c in cart:
        if c["item_id"] == item_id:
            c["quantity"] += quantity
            return {"message": "Updated quantity", "cart": cart}

    cart.append({"item_id": item_id, "quantity": quantity})
    return {"message": "Added to cart", "cart": cart}

@app.get("/cart")
def view_cart():
    total = 0
    for c in cart:
        item = find_menu_item(c["item_id"])
        total += item["price"] * c["quantity"]

    return {"cart": cart, "grand_total": total}

# -----------------------------
# Q15 Cart Delete + Checkout
# -----------------------------
@app.delete("/cart/{item_id}")
def remove_cart(item_id: int):
    for c in cart:
        if c["item_id"] == item_id:
            cart.remove(c)
            return {"message": "Item removed"}
    raise HTTPException(status_code=404, detail="Item not in cart")

class CheckoutRequest(BaseModel):
    customer_name: str
    delivery_address: str

@app.post("/cart/checkout", status_code=201)
def checkout(data: CheckoutRequest):
    global order_counter

    if not cart:
        raise HTTPException(status_code=400, detail="Cart empty")

    created_orders = []
    total = 0

    for c in cart:
        item = find_menu_item(c["item_id"])
        price = item["price"] * c["quantity"]

        order = {
            "order_id": order_counter,
            "customer_name": data.customer_name,
            "item": item["name"],
            "quantity": c["quantity"],
            "total_price": price
        }

        orders.append(order)
        created_orders.append(order)
        total += price
        order_counter += 1

    cart.clear()

    return {"orders": created_orders, "grand_total": total}

# -----------------------------
# Q16 Search
# -----------------------------
@app.get("/menu-search")
def search_menu(keyword: str):
    results = [i for i in menu if keyword.lower() in i["name"].lower() or keyword.lower() in i["category"].lower()]
    if not results:
        return {"message": "No items found"}
    return {"items": results, "total_found": len(results)}

# -----------------------------
# Q17 Sort
# -----------------------------
@app.get("/menu-sort")
def sort_menu(sort_by: str = "price", order: str = "asc"):
    if sort_by not in ["price", "name", "category"]:
        raise HTTPException(status_code=400, detail="Invalid sort_by")

    if order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Invalid order")

    sorted_menu = sorted(menu, key=lambda x: x[sort_by], reverse=(order == "desc"))

    return {"sorted_by": sort_by, "order": order, "items": sorted_menu}

# -----------------------------
# Q18 Pagination
# -----------------------------
@app.get("/menu-page")
def paginate(page: int = Query(1, ge=1), limit: int = Query(3, ge=1, le=10)):
    start = (page - 1) * limit
    total = len(menu)
    total_pages = math.ceil(total / limit)

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": total_pages,
        "items": menu[start:start + limit]
    }

# -----------------------------
# Q19 Orders Search & Sort
# -----------------------------
@app.get("/orders/search")
def search_orders(customer_name: str):
    results = [o for o in orders if customer_name.lower() in o["customer_name"].lower()]
    return {"results": results}

@app.get("/orders/sort")
def sort_orders(order: str = "asc"):
    sorted_orders = sorted(orders, key=lambda x: x["total_price"], reverse=(order == "desc"))
    return {"orders": sorted_orders}

# -----------------------------
# Q20 Combined Browse
# -----------------------------
@app.get("/menu-browse")
def browse(
    keyword: Optional[str] = None,
    sort_by: str = "price",
    order: str = "asc",
    page: int = 1,
    limit: int = 4
):
    results = menu

    if keyword:
        results = [i for i in results if keyword.lower() in i["name"].lower()]

    results = sorted(results, key=lambda x: x[sort_by], reverse=(order == "desc"))

    start = (page - 1) * limit
    total = len(results)

    return {
        "total": total,
        "page": page,
        "items": results[start:start + limit]
    }