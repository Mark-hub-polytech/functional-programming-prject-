# app.py 
import streamlit as st
import pandas as pd
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass
from functools import lru_cache, reduce

# ---------------------------
# Лабораториялық жұмыс #1: Өзгермейтін деректер құрылымдары
# ---------------------------
@dataclass(frozen=True)
class User:
    id: int
    username: str
    password: str
    is_admin: bool
    full_name: str
    email: str
    phone: str

@dataclass(frozen=True)
class Product:
    id: int
    name: str
    price: int
    stock: int
    description: str
    image: str
    category: str
    rating: float

@dataclass(frozen=True)
class CartItem:
    product_id: int
    quantity: int

@dataclass(frozen=True)
class Order:
    id: int
    user_id: int
    items: Tuple[CartItem, ...]
    created_at: datetime
    status: str
    total: int
    address: str
    delivery_date: date

# ---------------------------
# Лабораториялық жұмыс #4: Функционалдық үлгілер (Option/Either)
# ---------------------------
class Option:
    def __init__(self, value=None, is_some=True):
        self.value = value
        self.is_some = is_some
    
    @staticmethod
    def some(value):
        return Option(value, True)
    
    @staticmethod
    def none():
        return Option(None, False)
    
    def map(self, func):
        if self.is_some:
            return Option.some(func(self.value))
        return Option.none()
    
    def get_or_else(self, default):
        return self.value if self.is_some else default
    
    def __str__(self):
        return f"Some({self.value})" if self.is_some else "None"

class Either:
    def __init__(self, value=None, is_right=True, error=None):
        self.value = value
        self.is_right = is_right
        self.error = error
    
    @staticmethod
    def right(value):
        return Either(value, True)
    
    @staticmethod
    def left(error):
        return Either(None, False, error)
    
    def map(self, func):
        if self.is_right:
            try:
                return Either.right(func(self.value))
            except Exception as e:
                return Either.left(str(e))
        return Either.left(self.error)
    
    def get_or_else(self, default):
        return self.value if self.is_right else default
    
    def __str__(self):
        return f"Right({self.value})" if self.is_right else f"Left({self.error})"

# ---------------------------
# Лабораториялық жұмыс #1: Таза функциялар және жоғары ретті функциялар
# ---------------------------
def format_price(num: int | float) -> str:
    """Таза функция: бағаны пішімдеу"""
    try:
        return f"{int(num):,} ₸"
    except Exception:
        return f"{num} ₸"

def get_product(products: List[Product], pid: int) -> Option:
    """Таза функция: Option типімен өнімді іздеу"""
    for p in products:
        if p.id == pid:
            return Option.some(p)
    return Option.none()

def calculate_total(items: List[CartItem], products: List[Product]) -> Either:
    """Таза функция: Either типімен қателерді өңдеу"""
    try:
        total = 0
        for item in items:
            product_option = get_product(products, item.product_id)
            if product_option.is_some:
                total += product_option.value.price * item.quantity
            else:
                return Either.left(f"Өнім {item.product_id} табылмады")
        return Either.right(total)
    except Exception as e:
        return Either.left(f"Есептеу қатесі: {str(e)}")

def filter_products(products: List[Product], predicate: Callable[[Product], bool]) -> List[Product]:
    """Жоғары ретті функция: сүзгілеу"""
    return list(filter(predicate, products))

def map_products(products: List[Product], mapper: Callable[[Product], Any]) -> List[Any]:
    """Жоғары ретті функция: карталау"""
    return list(map(mapper, products))

def reduce_products(products: List[Product], reducer: Callable[[Any, Product], Any], initial: Any) -> Any:
    """Жоғары ретті функция: азайту"""
    return reduce(reducer, products, initial)

# ---------------------------
# Лабораториялық жұмыс #2: Конфигуратор-closure функциялары
# ---------------------------
def create_category_filter(category: str) -> Callable[[Product], bool]:
    """Closure: категория бойынша сүзгі жасау"""
    def filter_by_category(product: Product) -> bool:
        return product.category == category
    return filter_by_category

def create_price_range_filter(min_price: int, max_price: int) -> Callable[[Product], bool]:
    """Closure: баға диапазоны бойынша сүзгі жасау"""
    def filter_by_price(product: Product) -> bool:
        return min_price <= product.price <= max_price
    return filter_by_price

def create_search_filter(search_query: str) -> Callable[[Product], bool]:
    """Closure: іздеу сүзгісін жасау"""
    def filter_by_search(product: Product) -> bool:
        return search_query.lower() in product.name.lower() or search_query.lower() in product.description.lower()
    return filter_by_search

# ---------------------------
# Лабораториялық жұмыс #2: Рекурсивті алгоритмдер
# ---------------------------
def recursive_category_tree(products: List[Product], current_level: int = 0) -> List[str]:
    """Рекурсивті функция: категория ағашының құрылымы"""
    if not products:
        return []
    
    categories = set(p.category for p in products)
    result = []
    
    for category in sorted(categories):
        result.append("  " * current_level + f"📂 {category}")
        category_products = filter_products(products, lambda p: p.category == category)
        for product in category_products:
            result.append("  " * (current_level + 1) + f"📦 {product.name} - {format_price(product.price)}")
    
    return result

def recursive_total_value(products: List[Product], index: int = 0, total: int = 0) -> int:
    """Рекурсивті функция: жалпы инвентарлық құнды есептеу"""
    if index >= len(products):
        return total
    
    product = products[index]
    product_value = product.price * product.stock
    return recursive_total_value(products, index + 1, total + product_value)

# ---------------------------
# Лабораториялық жұмыс #3: Мемоизация
# ---------------------------
@lru_cache(maxsize=128)
def expensive_product_analysis(products_data: tuple) -> Dict[str, Any]:
    """
    Қымбатты есептеу функциясы: мемоизациямен
    products_data параметрі tuple түрінде берілуі керек (өйткені lru_cache hashable параметрлерді қажет етеді)
    """
    # Өнімдерді қайта құру
    products = [Product(*p) for p in products_data]
    
    # Қымбат есептеуді имитациялау
    import time
    time.sleep(0.5)  # Өңдеу уақытын имитациялау
    
    # Күрделі талдау
    total_products = len(products)
    total_value = recursive_total_value(products)
    total_stock = sum(p.stock for p in products)
    avg_price = total_value / total_stock if total_stock > 0 else 0
    categories = len(set(p.category for p in products))
    
    return {
        "total_products": total_products,
        "total_inventory_value": total_value,
        "average_price": avg_price,
        "unique_categories": categories,
        "analysis_time": datetime.now()
    }

# ---------------------------
# Параметрлерді орнату
# ---------------------------
st.set_page_config(
    page_title="MarkStore - Электрондық дүкен",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- CSS STYLE ----------------
st.markdown("""
<style>
/* Негізгі стильдер */
.main { background-color: #f8fafc; }
.stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
/* Барлық мәтіндерді қара түске өзгерту */
* { color: #000000 !important; }
h1, h2, h3, h4, h5, h6, p, div, span, label, input, textarea, select, button, a {
  color: #000000 !important;
}
/* Сайдбар стильдері (ескерту: streamlit класс атаулары версияға тәуелді) */
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #4b6cb7 0%, #182848 100%);
}
section[data-testid="stSidebar"] * { color: #000000 !important; }
section[data-testid="stSidebar"] .stButton>button {
  background: rgba(255,255,255,0.1);
  border: 1px solid rgba(255,255,255,0.2);
  color: #000000 !important;
}
section[data-testid="stSidebar"] .stButton>button:hover {
  background: rgba(255,255,255,0.2);
}
/* Карточкалар */
.product-card {
  border: 1px solid #e2e8f0; border-radius: 16px; padding: 20px;
  background: #ffffff; text-align: center; transition: all 0.3s ease;
  box-shadow: 0 4px 6px rgba(0,0,0,0.04); margin-bottom: 25px;
  height: 100%; display: flex; flex-direction: column; justify-content: space-between;
}
.product-card:hover { transform: translateY(-5px); box-shadow: 0 20px 25px rgba(0,0,0,0.1); }
/* Баға */
.price-badge {
  display:inline-block; background: linear-gradient(135deg,#667eea 0%,#764ba2 100%);
  color:white !important; padding:10px 20px; border-radius:25px; font-weight:bold; margin:12px 0;
  font-size:18px; box-shadow:0 4px 6px rgba(0,0,0,0.1);
}
/* Батырмалар */
.stButton > button {
  border-radius: 12px !important; padding: 12px 28px !important;
  font-weight: 600 !important; transition: all 0.3s ease !important; width: 100%;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  color: #000000 !important;
}
.stButton > button:first-child { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border: none !important; }
.stButton > button:first-child:hover { background: linear-gradient(135deg, #764ba2 0%, #667eea 100%); transform: scale(1.03); box-shadow: 0 6px 8px rgba(0,0,0,0.15); }
/* Тақырыптар */
h1, h2, h3 { color: #000000 !important; font-weight: 700; }
/* Хедер */
.header {
  background: linear-gradient(90deg, #4b6cb7 0%, #182848 100%);
  padding: 25px; border-radius: 16px; color: #000000 !important; margin-bottom: 35px;
  box-shadow: 0 10px 15px rgba(0,0,0,0.1);
}
/* Админ карточкалары */
.admin-stats {
  background:#ffffff; border-radius:16px; padding:25px; margin-bottom:25px;
  border-left:6px solid #4b6cb7; box-shadow:0 4px 6px rgba(0,0,0,0.05);
}
/* Хабарламалар, кестелер */
.stAlert { border-radius: 12px; }
.stDataFrame { border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
/* Футер */
.footer { text-align:center; margin-top:60px; padding:25px; color:#000000 !important; font-size:14px; }
/* Сайдбардағы мәтіндерді қара түске өзгерту */
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] h4,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] div {
  color: #000000 !important;
}
/* Хедердегі мәтіндерді қара түске өзгерту */
.header h1,
.header p {
  color: #000000 !important;
}
/* Инпуттардағы мәтіндерді қара түске өзгерту */
.stTextInput input,
.stTextArea textarea,
.stSelectbox select,
.stNumberInput input {
  color: #000000 !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Көмекші функциялар
# ---------------------------
def format_price_old(num: int | float) -> str:
    try:
        return f"{int(num):,} ₸"
    except Exception:
        return f"{num} ₸"

def get_product_old(pid):
    return next((p for p in st.session_state["products"] if p["id"] == pid), None)

def ensure_session_keys():
    for key, default in [
        ("users", []), ("products", []), ("orders", []), ("cart", []),
        ("me", None), ("current_page", "🏪 Негізгі бет")
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

ensure_session_keys()

# ---------------------------
# 1) In-memory деректер (алғашқы толтыру)
# ---------------------------
if not st.session_state["users"]:
    st.session_state["users"] = [
        {"id":1,"username":"admin","password":"Admin123","is_admin":True,"full_name":"Admin User", "email":"admin@markstore.kz", "phone":"+7 777 123 4567"},
        {"id":2,"username":"ali","password":"Ali123","is_admin":False,"full_name":"Ali Orinbasar", "email":"ali@mail.kz", "phone":"+7 707 765 4321"},
        {"id":3,"username":"bobo","password":"Bobo123","is_admin":False,"full_name":"Bobo User", "email":"bobo@example.com", "phone":"+7 705 123 4567"},
    ]

if not st.session_state["products"]:
    st.session_state["products"] = [
        {"id":1,"name":"AirPods Pro","price":4990,"stock":10,"description":"Wireless earbuds with great sound","image":"https://via.placeholder.com/600x400/4b6cb7/ffffff?text=AirPods+Pro","category":"Ақпараттық техника", "rating":4.8},
        {"id":2,"name":"AirPods 3","price":4490,"stock":8,"description":"True wireless earbuds","image":"https://via.placeholder.com/600x400/182848/ffffff?text=AirPods+3","category":"Ақпараттық техника", "rating":4.5},
        {"id":3,"name":"AirPods 4","price":7990,"stock":5,"description":"Next-gen AirPods","image":"https://via.placeholder.com/600x400/36d1dc/ffffff?text=AirPods+4","category":"Ақпараттық техника", "rating":4.9},
        {"id":4,"name":"iPhone 14","price":399990,"stock":7,"description":"Latest iPhone","image":"https://via.placeholder.com/600x400/5b86e5/ffffff?text=iPhone+14","category":"Телефондар", "rating":4.7},
        {"id":5,"name":"Samsung Galaxy","price":299990,"stock":12,"description":"Android flagship","image":"https://via.placeholder.com/600x400/2c3e50/ffffff?text=Galaxy","category":"Телефондар", "rating":4.6},
        {"id":6,"name":"MacBook Pro","price":699990,"stock":6,"description":"Powerful laptop for professionals","image":"https://via.placeholder.com/600x400/667eea/ffffff?text=MacBook+Pro","category":"Ноутбуктер", "rating":4.9},
    ]

# ---------------------------
# 2) User login/register
# ---------------------------
st.sidebar.markdown("""
<div style="text-align:center; margin-bottom:30px;">
    <h1 style="color:#000000; margin-bottom:5px;">🛒 MarkStore</h1>
    <p style="color:#000000;">Электрондық дүкен</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")

me = st.session_state["me"]

if me is None:
    auth_tab = st.sidebar.radio("Аутентификация", ["Кіру", "Тіркелу", "Функционалдық талдау"], label_visibility="collapsed")
    if auth_tab == "Кіру":
        with st.sidebar.form("login_form"):
            st.subheader("👤 Жүйеге кіру")
            username = st.text_input("Пайдаланушы аты", key="login_user")
            password = st.text_input("Құпия сөз", type="password", key="login_pass")
            login_btn = st.form_submit_button("✅ Кіру", use_container_width=True)
            if login_btn:
                user = next((u for u in st.session_state["users"] if u["username"]==username and u["password"]==password), None)
                if user:
                    st.session_state["me"] = user
                    st.sidebar.success(f"Қош келдіңіз, {user['full_name']}!")
                    st.rerun()
                else:
                    st.sidebar.error("Қате логин немесе пароль")
    elif auth_tab == "Тіркелу":
        with st.sidebar.form("register_form"):
            st.subheader("😊 Жаңа аккаунт жасау")
            new_user = st.text_input("Пайдаланушы аты")
            new_pass = st.text_input("Құпия сөз", type="password")
            confirm_pass = st.text_input("Құпия сөзді растау", type="password")
            full_name = st.text_input("Аты-жөні")
            email = st.text_input("Email")
            phone = st.text_input("Телефон")
            register_btn = st.form_submit_button("✅ Тіркелу", use_container_width=True)
            if register_btn:
                if len(new_user.strip()) < 3:
                    st.sidebar.error("Пайдаланушы аты тым қысқа")
                elif new_pass != confirm_pass:
                    st.sidebar.error("Құпия сөздер сәйкес емес!")
                elif any(u["username"]==new_user for u in st.session_state["users"]):
                    st.sidebar.error("Бұл пайдаланушы аты бос емес")
                else:
                    uid = max(u["id"] for u in st.session_state["users"])+1
                    user = {"id":uid,"username":new_user,"password":new_pass,"is_admin":False,
                            "full_name":full_name or new_user, "email":email, "phone":phone}
                    st.session_state["users"].append(user)
                    st.session_state["me"] = user
                    st.sidebar.success("Сіз сәтті тіркелдіңіз! 🎉")
                    st.rerun()
    else:
        st.sidebar.subheader("🔬 Функционалдық талдау")
        st.sidebar.info("Бұл бөлімде функционалдық бағдарламау принциптері қолданылған:")
        st.sidebar.write("• ✅ Таза функциялар")
        st.sidebar.write("• ✅ Өзгермейтін деректер")
        st.sidebar.write("• ✅ Жоғары ретті функциялар")
        st.sidebar.write("• ✅ Рекурсия және мемоизация")
        st.sidebar.write("• ✅ Option/Either монадтары")
else:
    st.sidebar.markdown(f"""
    <div style="background:rgba(255,255,255,0.1); padding:15px; border-radius:12px; margin-bottom:20px;">
        <h4 style="color:#000000; margin:0;">👋 Қош келдіңіз!</h4>
        <p style="color:#000000; margin:5px 0 0 0;"><b>{me['full_name']}</b></p>
        <p style="color:#000000; margin:0;">{me.get('email','')}</p>
    </div>
    """, unsafe_allow_html=True)
    if st.sidebar.button("🚪 Жүйеден шығу", use_container_width=True):
        del st.session_state["me"]
        st.rerun()

st.sidebar.markdown("---")

# ---------------------------
# 3) Main Navigation
# ---------------------------
st.sidebar.subheader("🧭 Негізгі бөлімдер")
nav_options = ["🏪 Негізгі бет", "🛒 Себет", "📦 Тапсырыстарым", "👤 Профиль"]
if me and me.get("is_admin", False):
    nav_options.append("⚙️ Админ панелі")

# Навигация батырмалары
for i, option in enumerate(nav_options):
    if st.sidebar.button(option, key=f"nav_{i}", use_container_width=True):
        st.session_state.current_page = option

# Әдепкі бет
if "current_page" not in st.session_state:
    st.session_state.current_page = "🏪 Негізгі бет"

# ---------------------------
# Хедер
# ---------------------------
st.markdown(f"""
<div class="header">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
            <h1 style="color:#000000; margin:0;">🛒 MarkStore</h1>
            <p style="color:#000000; margin:0;">Қазақстандық жеңіл интернет-дүкен</p>
        </div>
        <div style="display:flex; gap:15px;">
            <div style="background:rgba(255,255,255,0.2); padding:10px 15px; border-radius:10px;">
                <p style="margin:0; color:#000000;">📦 {len(st.session_state['cart'])} зат</p>
            </div>
            <div style="background:rgba(255,255,255,0.2); padding:10px 15px; border-radius:10px;">
                <p style="margin:0; color:#000000;">👥 {len(st.session_state['users'])} пайдаланушы</p>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------
# 4) Негізгі бет (каталог)
# ---------------------------
if st.session_state.current_page == "🏪 Негізгі бет":
    st.header("🎁 Өнімдер каталогы")
    
    # Лабораториялық жұмыс #2: Функционалдық талдау бөлімі
    st.subheader("📊 Функционалдық талдау")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Категория ағашы (рекурсивті):**")
        # Өнімдерді Product нысандарына түрлендіру
        products_data = st.session_state["products"]
        products = [Product(p["id"], p["name"], p["price"], p["stock"], 
                           p["description"], p["image"], p["category"], p["rating"]) 
                   for p in products_data]
        category_tree = recursive_category_tree(products)
        for line in category_tree:
            st.text(line)
    
    with col2:
        st.write("**Инвентарлық құн (рекурсивті):**")
        total_value = recursive_total_value(products)
        st.metric("Жалпы инвентарлық құн", format_price(total_value))
        
        # Лабораториялық жұмыс #3: Мемоизацияны көрсету
        st.write("**Қымбат талдау (мемоизациямен):**")
        if st.button("🔄 Талдауды орындау"):
            with st.spinner("Талдау орындалуда..."):
                # Өнімдерді tuple түріне түрлендіру (lru_cache үшін hashable болуы керек)
                products_tuple = tuple((p.id, p.name, p.price, p.stock, p.description, 
                                      p.image, p.category, p.rating) for p in products)
                analysis = expensive_product_analysis(products_tuple)
                st.metric("Өнімдер саны", analysis["total_products"])
                st.metric("Инвентарлық құн", format_price(analysis["total_inventory_value"]))
                st.metric("Орташа баға", format_price(analysis["average_price"]))
                st.metric("Категориялар", analysis["unique_categories"])
    
    st.header("🎁 Өнімдер каталогы")
    filter_col1, filter_col2, filter_col3 = st.columns([2, 1, 1])
    with filter_col1:
        search_query = st.text_input("🔍 Өнімді іздеу", placeholder="Өнім атын енгізіңіз...")
    with filter_col2:
        categories = ["Барлығы"] + sorted(list(set(p["category"] for p in st.session_state["products"])))
        selected_category = st.selectbox("📂 Санат", categories)
    with filter_col3:
        sort_option = st.selectbox("📊 Сұрыптау", ["Әдетті", "Бағасы артуы", "Бағасы кемуі", "Жоғары рейтинг"])

    filtered_products = st.session_state["products"].copy()
    if search_query:
        filtered_products = [p for p in filtered_products if search_query.lower() in p["name"].lower()]
    if selected_category != "Барлығы":
        filtered_products = [p for p in filtered_products if p["category"] == selected_category]

    if sort_option == "Бағасы артуы":
        filtered_products.sort(key=lambda x: x["price"])
    elif sort_option == "Бағасы кемуі":
        filtered_products.sort(key=lambda x: x["price"], reverse=True)
    elif sort_option == "Жоғары рейтинг":
        filtered_products.sort(key=lambda x: x.get("rating", 0), reverse=True)

    if not filtered_products:
        st.warning("Өнімдер табылмады")
    else:
        cols = st.columns(3)
        for idx, p in enumerate(filtered_products):
            with cols[idx % 3]:
                rating_val = float(p.get("rating", 4))
                full_stars = int(rating_val)
                rating_str = "⭐" * full_stars + ("☆" if rating_val - full_stars >= 0.5 else "")
                st.markdown(f"""
                <div class="product-card">
                    <h3>{p['name']}</h3>
                    <img src='{p['image']}' width='100%' style='border-radius: 12px; margin: 10px auto; object-fit:cover;'>
                    <p style='font-size:14px; color:#000000; min-height: 40px;'>{p['description']}</p>
                    <div style="margin:10px 0; color:#000000;">{rating_str} ({p.get('rating', 4)})</div>
                    <span class="price-badge">{format_price_old(p['price'])}</span>
                    <p style="color:#000000;">📦 Қалдық: {p['stock']} дана</p>
                    <p style="color:#000000;">📂 {p['category']}</p>
                </div>
                """, unsafe_allow_html=True)

                if me and not me["is_admin"]:
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        qty = st.number_input(f"Саны {p['id']}", min_value=1, max_value=max(1,p["stock"]),
                                              value=1, key=f"qty_{p['id']}", label_visibility="collapsed")
                    with col2:
                        disabled = p["stock"] <= 0
                        if st.button("🛒 Себетке қосу", key=f"add_{p['id']}", use_container_width=True, disabled=disabled):
                            existing_item = next((item for item in st.session_state["cart"] if item["product_id"] == p["id"]), None)
                            if existing_item:
                                if existing_item["quantity"] + qty <= p["stock"]:
                                    existing_item["quantity"] += qty
                                    st.success(f"✅ {p['name']} себетке қосылды! (Барлығы: {existing_item['quantity']})")
                                else:
                                    st.error(f"❌ Қалдық жеткіліксіз! Қолжетімді: {p['stock']}")
                            else:
                                st.session_state["cart"].append({"product_id": p["id"], "quantity": qty})
                                st.success(f"✅ {p['name']} себетке қосылды!")
                            st.rerun()
                elif not me:
                    st.info("📝 Себетке қосу үшін жүйеге кіріңіз")

# ---------------------------
# 5) Себет
# ---------------------------
elif st.session_state.current_page == "🛒 Себет":
    st.header("🛒 Себет")
    if not me:
        st.info("📝 Себетті көру үшін жүйеге кіріңіз")
        if st.button("👤 Жүйеге кіру", use_container_width=True):
            st.session_state.current_page = "🏪 Негізгі бет"
            st.rerun()
    else:
        if not st.session_state["cart"]:
            st.info("😔 Сіздің себетіңіз бос")
            if st.button("🏪 Сатылымға өту", use_container_width=True):
                st.session_state.current_page = "🏪 Негізгі бет"
                st.rerun()
        else:
            cart_data = []
            total_cart = 0
            for item in st.session_state["cart"]:
                prod = get_product_old(item["product_id"])
                if not prod:
                    continue
                line_total = prod["price"] * item["quantity"]
                total_cart += line_total
                cart_data.append({
                    "Өнім": prod["name"],
                    "Бірлік бағасы": format_price_old(prod['price']),
                    "Саны": item["quantity"],
                    "Жалпы": format_price_old(line_total)
                })

            st.dataframe(pd.DataFrame(cart_data), use_container_width=True)
            st.markdown(f"### 💰 Жалпы сома: **{format_price_old(total_cart)}**")

            with st.expander("🚚 Жеткізу мәліметтері"):
                col1, col2 = st.columns(2)
                with col1:
                    delivery_address = st.text_input("Жеткізу мекенжайы", value="Алматы, Абай көшесі 1")
                with col2:
                    min_d = date.today()
                    delivery_date = st.date_input("Жеткізу күні", min_value=min_d, value=min_d)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🧹 Себетті тазалау", use_container_width=True):
                    st.session_state["cart"] = []
                    st.success("✅ Себет тазаланды!")
                    st.rerun()
            with col2:
                if st.button("✅ Тапсырыс беру", type="primary", use_container_width=True):
                    order_id = len(st.session_state["orders"]) + 1
                    order = {
                        "id": order_id,
                        "user_id": me["id"],
                        "items": [i.copy() for i in st.session_state["cart"]],
                        "created_at": datetime.now(),
                        "status": "pending",
                        "total": total_cart,
                        "address": delivery_address,
                        "delivery_date": delivery_date
                    }
                    st.session_state["orders"].append(order)
                    # Қалдықтарды азайту
                    for item in st.session_state["cart"]:
                        product = get_product_old(item["product_id"])
                        if product:
                            product["stock"] = max(0, product["stock"] - item["quantity"])
                    st.session_state["cart"] = []
                    st.success(f"🎉 Тапсырыс №{order_id} сәтті қабылданды!")
                    st.balloons()
                    st.info(f"📦 Тапсырыс №{order_id}. Жеткізу күні: {delivery_date}")
                    st.rerun()

# ---------------------------
# 6) Тапсырыстарым
# ---------------------------
elif st.session_state.current_page == "📦 Тапсырыстарым":
    st.header("📦 Менің тапсырыстарым")
    if not me:
        st.info("📝 Тапсырыстарды көру үшін жүйеге кіріңіз")
        if st.button("👤 Жүйеге кіру", use_container_width=True):
            st.session_state.current_page = "🏪 Негізгі бет"
            st.rerun()
    else:
        my_orders = [o for o in st.session_state["orders"] if o["user_id"] == me["id"]]
        if not my_orders:
            st.info("😔 Сізде әлі тапсырыс жоқ")
            if st.button("🏪 Сатылымға өту", use_container_width=True):
                st.session_state.current_page = "🏪 Негізгі бет"
                st.rerun()
        else:
            my_orders.sort(key=lambda x: x["created_at"], reverse=True)
            for o in my_orders:
                status_text = o["status"]
                if status_text == "pending":
                    status_display = "🟡 Күтуде"
                elif status_text == "completed":
                    status_display = "🟢 Аяқталды"
                elif status_text == "shipped":
                    status_display = "🚚 Жолға шықты"
                else:
                    status_display = f"🔵 {status_text}"

                with st.expander(f"📝 Тапсырыс №{o['id']} - {status_display} - {o['created_at'].strftime('%Y-%m-%d %H:%M')}"):
                    items = []
                    for it in o["items"]:
                        p = get_product_old(it["product_id"])
                        if not p:
                            continue
                        line_total = p["price"] * it["quantity"]
                        items.append({
                            "Өнім": p["name"],
                            "Саны": it["quantity"],
                            "Бағасы": format_price_old(p['price']),
                            "Жалпы": format_price_old(line_total)
                        })
                    st.table(pd.DataFrame(items))
                    st.markdown(f"**💰 Тапсырыс сомасы: {format_price_old(o['total'])}**")
                    if "address" in o:
                        st.markdown(f"**🏠 Жеткізу мекенжайы: {o['address']}**")
                    if "delivery_date" in o:
                        st.markdown(f"**📅 Жеткізу күні: {o['delivery_date']}**")

# ---------------------------
# 7) Профиль
# ---------------------------
elif st.session_state.current_page == "👤 Профиль":
    st.header("👤 Профиль")
    if not me:
        st.info("📝 Профильді көру үшін жүйеге кіріңіз")
        if st.button("👤 Жүйеге кіру", use_container_width=True):
            st.session_state.current_page = "🏪 Негізгі бет"
            st.rerun()
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("👤 Сіз туралы ақпарат")
            with st.form("profile_form"):
                full_name = st.text_input("Аты-жөні", value=me["full_name"])
                email = st.text_input("Email", value=me.get("email", ""))
                phone = st.text_input("Телефон", value=me.get("phone", ""))
                if st.form_submit_button("✅ Профильді жаңарту", use_container_width=True):
                    for user in st.session_state["users"]:
                        if user["id"] == me["id"]:
                            user["full_name"] = full_name.strip() or user["full_name"]
                            user["email"] = email
                            user["phone"] = phone
                    st.session_state["me"] = next(u for u in st.session_state["users"] if u["id"] == me["id"])
                    st.success("✅ Профиль сәтті жаңартылды!")
        with col2:
            st.subheader("📊 Статистика")
            my_orders = [o for o in st.session_state["orders"] if o["user_id"] == me["id"]]
            total_orders = len(my_orders)
            total_spent = sum(o['total'] for o in my_orders)
            colm1, colm2 = st.columns(2)
            with colm1: st.metric("📦 Жалпы тапсырыстар", total_orders)
            with colm2: st.metric("💰 Жалпы жұмсалған", format_price_old(total_spent))
            if total_orders > 0:
                st.subheader("📋 Соңғы тапсырыстар")
                recent_orders = sorted(my_orders, key=lambda x: x["created_at"], reverse=True)[:3]
                for o in recent_orders:
                    status_text = o["status"]
                    if status_text == "pending":
                        status_display = "🟡 Күтуде"
                    elif status_text == "completed":
                        status_display = "🟢 Аяқталды"
                    elif status_text == "shipped":
                        status_display = "🚚 Жолға шықты"
                    else:
                        status_display = f"🔵 {status_text}"
                    st.write(f"📦 Тапсырыс №{o['id']} - {status_display} - {format_price_old(o['total'])}")

# ---------------------------
# 8) Админ панелі
# ---------------------------
elif st.session_state.current_page == "⚙️ Админ панелі":
    st.header("⚙️ Админ панелі")
    if not me or not me.get("is_admin", False):
        st.error("⛔ Бұл бөлімге тек админ кіре алады")
    else:
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Тапсырыстар", "📈 Сатылым статистикасы", "🎁 Өнімдерді басқару", "👥 Пайдаланушылар"])

        # -------- Тапсырыстар
        with tab1:
            st.subheader("📊 Барлық тапсырыстар")
            if not st.session_state["orders"]:
                st.info("😔 Тапсырыстар жоқ")
            else:
                orders_list = []
                total_revenue = 0
                for o in st.session_state["orders"]:
                    user = next((u for u in st.session_state["users"] if u["id"] == o["user_id"]), None)
                    status_text = o["status"]
                    if status_text == "pending":
                        status_display = "Күтуде"
                    elif status_text == "completed":
                        status_display = "Аяқталды"
                    elif status_text == "shipped":
                        status_display = "Жолға шықты"
                    else:
                        status_display = status_text
                    orders_list.append({
                        "Тапсырыс ID": o["id"],
                        "Пайдаланушы": user["full_name"] if user else "Белгісіз",
                        "Зат саны": sum(i["quantity"] for i in o["items"]),
                        "Жалпы": format_price_old(o["total"]),
                        "Статус": status_display,
                        "Күні": o["created_at"].strftime("%Y-%m-%d %H:%M")
                    })
                    total_revenue += o["total"]

                st.dataframe(pd.DataFrame(orders_list), use_container_width=True)

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown(f'<div class="admin-stats"><h3>📦 Жалпы тапсырыстар</h3><h2>{len(st.session_state["orders"])}</h2></div>', unsafe_allow_html=True)
                with col2:
                    st.markdown(f'<div class="admin-stats"><h3>💰 Жалпы табыс</h3><h2>{format_price_old(total_revenue)}</h2></div>', unsafe_allow_html=True)
                with col3:
                    pending_orders = len([o for o in st.session_state["orders"] if o["status"] == "pending"])
                    st.markdown(f'<div class="admin-stats"><h3>⏳ Күтудегі тапсырыстар</h3><h2>{pending_orders}</h2></div>', unsafe_allow_html=True)
                with col4:
                    completed_orders = len([o for o in st.session_state["orders"] if o["status"] == "completed"])
                    st.markdown(f'<div class="admin-stats"><h3>✅ Орындалған тапсырыстар</h3><h2>{completed_orders}</h2></div>', unsafe_allow_html=True)

                st.subheader("🔄 Тапсырыс статусын өзгерту")
                order_ids = [o["id"] for o in st.session_state["orders"]]
                if order_ids:
                    selected_order = st.selectbox("Тапсырыс таңдаңыз", order_ids, key="adm_sel_order")
                    new_status = st.selectbox("Жаңа статус", ["pending", "shipped", "completed"], key="adm_new_status")
                    if st.button("✅ Статусты жаңарту", use_container_width=True):
                        for order in st.session_state["orders"]:
                            if order["id"] == selected_order:
                                order["status"] = new_status
                        st.success(f"✅ Тапсырыс №{selected_order} статусы жаңартылды!")
                        st.rerun()

        # -------- Сатылым статистикасы
        with tab2:
            st.subheader("📈 Сатылым статистикасы")
            sales = []
            for p in st.session_state["products"]:
                total_qty = sum(it["quantity"] for o in st.session_state["orders"] for it in o["items"] if it["product_id"] == p["id"])
                revenue = sum(it["quantity"] * p["price"] for o in st.session_state["orders"] for it in o["items"] if it["product_id"] == p["id"])
                sales.append({"Өнім": p["name"], "Сатылым саны": total_qty, "Табыс": revenue})

            df_sales = pd.DataFrame(sales)
            if not df_sales.empty:
                col1, col2 = st.columns(2)
                with col1:
                    st.write("#### Сатылым кестесі")
                    # Көрнекі баға
                    df_view = df_sales.copy()
                    df_view["Табыс"] = df_view["Табыс"].apply(format_price_old)
                    st.dataframe(df_view, use_container_width=True)
                with col2:
                    st.write("#### Табыс бойынша диаграмма")
                    chart_data = pd.DataFrame({'Өнім': df_sales['Өнім'], 'Табыс': df_sales['Табыс']})
                    st.bar_chart(chart_data.set_index('Өнім'))
            else:
                st.info("😔 Сатылым статистикасы жоқ")

        # -------- Өнімдерді басқару
        with tab3:
            st.subheader("🎁 Өнімдерді басқару")

            # Жаңа өнім қосу
            with st.form("add_product_form"):
                st.write("#### 🆕 Жаңа өнім қосу")
                col1, col2 = st.columns(2)
                with col1:
                    new_name = st.text_input("Атауы")
                    new_price = st.number_input("Бағасы (₸)", min_value=0, step=10, value=0)
                    new_stock = st.number_input("Қалдық (дана)", min_value=0, step=1, value=0)
                    new_category = st.text_input("Санат", value="Әр түрлі")
                with col2:
                    new_desc = st.text_area("Сипаттама", height=100, value="—")
                    new_image = st.text_input("Сурет URL", value="https://via.placeholder.com/600x400/cccccc/000000?text=Product")
                    new_rating = st.slider("Рейтинг", min_value=0.0, max_value=5.0, step=0.1, value=4.5)

                if st.form_submit_button("➕ Қосу", use_container_width=True):
                    if len(new_name.strip()) == 0:
                        st.error("Атауы бос болмауы керек")
                    else:
                        new_id = (max([p["id"] for p in st.session_state["products"]]) + 1) if st.session_state["products"] else 1
                        st.session_state["products"].append({
                            "id": new_id, "name": new_name.strip(), "price": int(new_price),
                            "stock": int(new_stock), "description": new_desc.strip(),
                            "image": new_image.strip(), "category": new_category.strip() or "Әр түрлі",
                            "rating": float(new_rating)
                        })
                        st.success(f"✅ «{new_name}» қосылды!")
                        st.rerun()

            st.write("----")
            st.write("#### ✏️ Өңдеу / 🗑️ Өшіру")

            if not st.session_state["products"]:
                st.info("Өнімдер жоқ")
            else:
                # Іздеу + сүзгі
                pcol1, pcol2, pcol3 = st.columns([2,1,1])
                with pcol1:
                    p_search = st.text_input("Өнімді іздеу (атауы бойынша)", key="prod_search")
                with pcol2:
                    p_cats = ["Барлығы"] + sorted(list(set(p["category"] for p in st.session_state["products"])))
                    p_cat = st.selectbox("Санат", p_cats, key="prod_cat_filter")
                with pcol3:
                    p_sort = st.selectbox("Сұрыптау", ["Әдепкі", "Бағасы↑", "Бағасы↓", "Қалдық↑", "Қалдық↓"], key="prod_sort")

                prods = st.session_state["products"].copy()
                if p_search:
                    prods = [p for p in prods if p_search.lower() in p["name"].lower()]
                if p_cat != "Барлығы":
                    prods = [p for p in prods if p["category"] == p_cat]

                if p_sort == "Бағасы↑":
                    prods.sort(key=lambda x: x["price"])
                elif p_sort == "Бағасы↓":
                    prods.sort(key=lambda x: x["price"], reverse=True)
                elif p_sort == "Қалдық↑":
                    prods.sort(key=lambda x: x["stock"])
                elif p_sort == "Қалдық↓":
                    prods.sort(key=lambda x: x["stock"], reverse=True)

                # Әр өнімге inline форма
                for p in prods:
                    with st.expander(f"🧩 {p['name']} — {format_price_old(p['price'])} | Қалдық: {p['stock']} | Категория: {p['category']}"):
                        c1, c2 = st.columns([2,1])
                        with c1:
                            with st.form(f"edit_form_{p['id']}", clear_on_submit=False):
                                ec1, ec2 = st.columns(2)
                                with ec1:
                                    e_name = st.text_input("Атауы", value=p["name"], key=f"e_name_{p['id']}")
                                    e_price = st.number_input("Бағасы (₸)", min_value=0, step=10, value=int(p["price"]), key=f"e_price_{p['id']}")
                                    e_stock = st.number_input("Қалдық (дана)", min_value=0, step=1, value=int(p["stock"]), key=f"e_stock_{p['id']}")
                                    e_category = st.text_input("Санат", value=p["category"], key=f"e_cat_{p['id']}")
                                with ec2:
                                    e_desc = st.text_area("Сипаттама", value=p["description"], height=100, key=f"e_desc_{p['id']}")
                                    e_image = st.text_input("Сурет URL", value=p["image"], key=f"e_img_{p['id']}")
                                    e_rating = st.slider("Рейтинг", min_value=0.0, max_value=5.0, step=0.1, value=float(p.get("rating", 4.5)), key=f"e_rate_{p['id']}")

                                col_save, col_del = st.columns(2)
                                with col_save:
                                    if st.form_submit_button("💾 Сақтау", use_container_width=True):
                                        p["name"] = e_name.strip() or p["name"]
                                        p["price"] = int(e_price)
                                        p["stock"] = int(e_stock)
                                        p["category"] = e_category.strip() or p["category"]
                                        p["description"] = e_desc.strip()
                                        p["image"] = e_image.strip()
                                        p["rating"] = float(e_rating)
                                        st.success("✅ Өзгерістер сақталды")
                                        st.rerun()
                                with col_del:
                                    if st.form_submit_button("🗑️ Өшіру", use_container_width=True):
                                        st.session_state["products"] = [x for x in st.session_state["products"] if x["id"] != p["id"]]
                                        st.warning(f"🗑️ «{p['name']}» өшірілді")
                                        st.rerun()
                        with c2:
                            st.image(p["image"], use_container_width=True)

        # -------- Пайдаланушылар
        with tab4:
            st.subheader("👥 Пайдаланушылар")
            if not st.session_state["users"]:
                st.info("Пайдаланушылар жоқ")
            else:
                ucol1, ucol2, ucol3 = st.columns([2,1,1])
                with ucol1:
                    u_search = st.text_input("Іздеу (аты/username/email)")
                with ucol2:
                    role_filter = st.selectbox("Рөл сүзгісі", ["Барлығы", "Админ", "Қарапайым"])
                with ucol3:
                    sort_user = st.selectbox("Сұрыптау", ["Әдепкі", "Аты-жөні", "Username"])

                users = st.session_state["users"].copy()
                if u_search:
                    q = u_search.lower()
                    users = [u for u in users if q in (u.get("full_name","").lower() + " " + u["username"].lower() + " " + u.get("email","").lower())]
                if role_filter == "Админ":
                    users = [u for u in users if u.get("is_admin")]
                elif role_filter == "Қарапайым":
                    users = [u for u in users if not u.get("is_admin")]

                if sort_user == "Аты-жөні":
                    users.sort(key=lambda x: x.get("full_name","").lower())
                elif sort_user == "Username":
                    users.sort(key=lambda x: x["username"].lower())

                data = []
                for u in users:
                    data.append({
                        "ID": u["id"],
                        "Аты-жөні": u.get("full_name",""),
                        "Username": u["username"],
                        "Email": u.get("email",""),
                        "Телефон": u.get("phone",""),
                        "Рөл": "Админ" if u.get("is_admin") else "Пайдаланушы"
                    })
                st.dataframe(pd.DataFrame(data), use_container_width=True)

                st.write("----")
                st.write("#### Рөл тағайындау / Құпиясөзді ауыстыру / Өшіру")

                if users:
                    uid_list = [u["id"] for u in users]
                    sel_uid = st.selectbox("Пайдаланушыны таңдаңыз (ID)", uid_list, key="user_manage_sel")
                    target = next((u for u in st.session_state["users"] if u["id"] == sel_uid), None)
                    if target:
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            make_admin = st.checkbox("Админ ету", value=bool(target.get("is_admin")), key="chk_admin")
                            if st.button("💼 Рөлді сақтау", use_container_width=True):
                                if target["id"] == me["id"] and not make_admin:
                                    st.error("Өзіңіздің админ құқығын шектеуге болмайды.")
                                else:
                                    target["is_admin"] = make_admin
                                    st.success("✅ Рөл жаңартылды")
                                    st.rerun()
                        with c2:
                            new_pass = st.text_input("Жаңа құпиясөз", type="password", key="new_pass_admin")
                            if st.button("🔑 Құпиясөзді ауыстыру", use_container_width=True):
                                if len(new_pass) < 4:
                                    st.error("Құпиясөз тым қысқа")
                                else:
                                    target["password"] = new_pass
                                    st.success("✅ Құпиясөз ауыстырылды")
                        with c3:
                            if st.button("🗑️ Пайдаланушыны өшіру", use_container_width=True):
                                if target["id"] == me["id"]:
                                    st.error("Өзіңізді өшіре алмайсыз.")
                                else:
                                    # Байланысты тапсырыстарды қалдыруға болады (тарих үшін)
                                    st.session_state["users"] = [u for u in st.session_state["users"] if u["id"] != target["id"]]
                                    st.warning("🗑️ Пайдаланушы өшірілді")
                                    st.rerun()

# ---------------------------
# Футер
# ---------------------------
st.markdown("""
<div class="footer">
  MarkStore © 2025 • Демонстрациялық нұсқа • Session-based деректер (қосымшаны қайта іске қосқанда тазарады)
</div>
""", unsafe_allow_html=True)