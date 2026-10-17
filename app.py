import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Bé Dâu Milk Tea", page_icon="🎀", layout="wide")

# ---------- Cute pink theme ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap');
html, body, [class*="css"] { font-family: 'Nunito', sans-serif; }
.stApp { background: linear-gradient(135deg, #fff7fb 0%, #ffeaf4 50%, #fff5fa 100%); color: #57384a; }
.block-container { padding-top: 1.4rem; max-width: 1250px; }
.hero { background: linear-gradient(120deg,#ff8fbd,#ffb8d4); border: 3px solid white; border-radius: 28px; padding: 24px 28px; color: white; box-shadow: 0 8px 24px #e78db633; }
.hero h1 { margin: 0; font-size: 2.2rem; font-weight: 900; }
.hero p { margin: 5px 0 0; font-size: 1rem; }
.pill { display:inline-block; background:#fff; color:#e65c98; border-radius:999px; padding:5px 12px; font-weight:800; margin-bottom:8px; }
.menu-card { background: rgba(255,255,255,.92); border: 2px solid #ffe0ed; border-radius: 20px; padding: 12px; margin-bottom: 10px; box-shadow: 0 5px 16px #db8eae12; }
.price { color:#e24f91; font-weight:900; font-size:1.05rem; }
.small { color:#9b7187; font-size:.85rem; }
div.stButton > button { border-radius: 14px; border: 1px solid #f7a9ca; background: #fff0f7; color:#c63f7b; font-weight:800; }
div.stButton > button:hover { background:#ff8fbd; color:white; border-color:#ff8fbd; }
div[data-testid="stMetric"] { background:#fff; border:2px solid #ffe0ed; border-radius:18px; padding:12px; }
div[data-testid="stMetricLabel"] { color:#a45c7e; }
hr { border-color:#ffd5e7; }
</style>
""", unsafe_allow_html=True)

MENU = [
    {"name":"Trà sữa trân châu đường đen","category":"Trà sữa","price":35000,"emoji":"🧋","image":"https://images.unsplash.com/photo-1558857563-b371033873b8?auto=format&fit=crop&w=700&q=85","desc":"Béo thơm, trân châu dai"},
    {"name":"Trà sữa truyền thống","category":"Trà sữa","price":29000,"emoji":"🥤","image":"https://images.unsplash.com/photo-1525385133512-2f3d320b4f9f?auto=format&fit=crop&w=700&q=85","desc":"Vị trà đậm dịu ngọt"},
    {"name":"Trà đào cam sả","category":"Trà trái cây","price":32000,"emoji":"🍑","image":"https://images.unsplash.com/photo-1556679343-c7306c1976bc?auto=format&fit=crop&w=700&q=85","desc":"Thanh mát, thơm trái cây"},
    {"name":"Trà vải hoa hồng","category":"Trà trái cây","price":33000,"emoji":"🌹","image":"https://images.unsplash.com/photo-1544145945-f90425340c7e?auto=format&fit=crop&w=700&q=85","desc":"Ngọt nhẹ, thơm dịu"},
    {"name":"Matcha latte","category":"Đá xay & latte","price":38000,"emoji":"🍵","image":"https://images.unsplash.com/photo-1515823064-d6e0c04616a7?auto=format&fit=crop&w=700&q=85","desc":"Matcha thơm, sữa mịn"},
    {"name":"Chocolate đá xay","category":"Đá xay & latte","price":40000,"emoji":"🍫","image":"https://images.unsplash.com/photo-1572490122747-3968b75cc699?auto=format&fit=crop&w=700&q=85","desc":"Chocolate đậm vị"},
    {"name":"Sữa tươi trân châu","category":"Trà sữa","price":36000,"emoji":"🥛","image":"https://images.unsplash.com/photo-1576092768241-dec231879fc3?auto=format&fit=crop&w=700&q=85","desc":"Sữa tươi béo thơm"},
    {"name":"Trà chanh mật ong","category":"Trà trái cây","price":25000,"emoji":"🍋","image":"https://images.unsplash.com/photo-1513558161293-c243a3e7f8e5?auto=format&fit=crop&w=700&q=85","desc":"Chua ngọt dễ uống"},
]
ADDONS = {"Trân châu đen":5000, "Trân châu trắng":7000, "Pudding trứng":7000, "Thạch trái cây":5000, "Kem cheese":10000}

if "cart" not in st.session_state:
    st.session_state.cart = []
if "orders" not in st.session_state:
    st.session_state.orders = []

st.markdown("""
<div class="hero">
  <span class="pill">🎀 TIỆM TRÀ SỮA NHỎ XINH</span>
  <h1>🍓 Bé Dâu Milk Tea</h1>
  <p>Chốt đơn ngọt ngào, tính tiền nhanh gọn! ♡</p>
</div>
""", unsafe_allow_html=True)

st.write("")
tab_order, tab_menu, tab_history = st.tabs(["🛍️ Bán hàng & tính tiền", "🧋 Thực đơn", "🧾 Lịch sử đơn"])

def money(n):
    return f"{int(n):,}đ".replace(",", ".")

with tab_order:
    left, right = st.columns([1.25, 0.85], gap="large")
    with left:
        st.subheader("💗 Chọn món cho khách")
        categories = ["Tất cả"] + sorted(set(x["category"] for x in MENU))
        category = st.selectbox("Lọc theo nhóm món", categories, key="filter_category")
        search = st.text_input("🔎 Tìm món", placeholder="Ví dụ: trà sữa, matcha...")
        shown = [x for x in MENU if (category == "Tất cả" or x["category"] == category) and search.lower() in x["name"].lower()]
        cols = st.columns(2)
        for i, item in enumerate(shown):
            with cols[i % 2]:
                st.markdown('<div class="menu-card">', unsafe_allow_html=True)
                try:
                    st.image(item["image"], use_container_width=True)
                except Exception:
                    st.markdown(f"<div style='font-size:70px;text-align:center'>{item['emoji']}</div>", unsafe_allow_html=True)
                st.markdown(f"**{item['emoji']} {item['name']}**")
                st.markdown(f"<span class='small'>{item['desc']}</span>", unsafe_allow_html=True)
                st.markdown(f"<div class='price'>{money(item['price'])}</div>", unsafe_allow_html=True)
                qty = st.number_input("Số lượng", min_value=1, max_value=20, value=1, step=1, key=f"qty_{item['name']}")
                if st.button(f"＋ Thêm món", key=f"add_{item['name']}", use_container_width=True):
                    st.session_state.cart.append({"name":item["name"], "price":item["price"], "qty":int(qty), "addons":[], "note":""})
                    st.toast(f"Đã thêm {item['name']} vào đơn 💕")
                st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.subheader("🧺 Đơn hàng hiện tại")
        customer = st.text_input("Tên khách (không bắt buộc)", placeholder="Tên khách hàng")
        if not st.session_state.cart:
            st.info("Đơn hàng đang trống nè. Chọn món bên trái để bắt đầu nhé! 🌷")
        else:
            for idx, row in enumerate(st.session_state.cart):
                with st.container(border=True):
                    c1, c2 = st.columns([3,1])
                    with c1:
                        st.markdown(f"**{row['name']}**")
                        st.caption(f"{money(row['price'])} / ly")
                    with c2:
                        st.markdown(f"**× {row['qty']}**")
                    new_qty = st.number_input("Chỉnh số lượng", min_value=1, max_value=50, value=row["qty"], key=f"cartqty_{idx}")
                    row["qty"] = int(new_qty)
                    row["addons"] = st.multiselect("Topping", list(ADDONS.keys()), default=row.get("addons", []), key=f"addons_{idx}")
                    row["note"] = st.text_input("Ghi chú món", value=row.get("note",""), placeholder="Ít đá, 30% đường...", key=f"note_{idx}")
                    if st.button("🗑️ Xóa món này", key=f"remove_{idx}"):
                        st.session_state.cart.pop(idx)
                        st.rerun()
            subtotal = sum((r["price"] + sum(ADDONS[a] for a in r["addons"])) * r["qty"] for r in st.session_state.cart)
            discount_pct = st.selectbox("Ưu đãi", [0, 5, 10, 15, 20], format_func=lambda x: "Không giảm" if x == 0 else f"Giảm {x}%", key="discount")
            discount = round(subtotal * discount_pct / 100)
            service_fee = st.number_input("Phụ thu (VNĐ)", min_value=0, value=0, step=1000)
            total = subtotal - discount + service_fee
            st.markdown("---")
            st.markdown(f"**Tạm tính:** {money(subtotal)}")
            st.markdown(f"**Giảm giá:** −{money(discount)}")
            st.markdown(f"### 💖 Tổng thanh toán: {money(total)}")
            paid = st.number_input("Khách đưa (VNĐ)", min_value=0, value=int(total), step=1000, key="paid")
            change = max(0, int(paid) - int(total))
            st.metric("Tiền thối lại", money(change))
            if paid < total:
                st.warning(f"Khách còn thiếu {money(total-paid)}")
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("✅ Hoàn tất đơn", use_container_width=True, type="primary"):
                    st.session_state.orders.append({
                        "time":datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "customer":customer or "Khách lẻ",
                        "items":[dict(r) for r in st.session_state.cart],
                        "subtotal":subtotal,"discount":discount,"total":total,"paid":int(paid),"change":change
                    })
                    st.session_state.cart = []
                    st.success("Đã lưu đơn hàng thành công! 🎉")
                    st.rerun()
            with col_b:
                if st.button("🧹 Xóa toàn bộ", use_container_width=True):
                    st.session_state.cart = []
                    st.rerun()

with tab_menu:
    st.subheader("🌸 Menu của tiệm")
    st.caption("Giá mẫu có thể chỉnh sửa trong danh sách MENU ở đầu file app.py.")
    cols = st.columns(4)
    for i, item in enumerate(MENU):
        with cols[i % 4]:
            st.image(item["image"], use_container_width=True)
            st.markdown(f"**{item['emoji']} {item['name']}**")
            st.caption(item["category"])
            st.markdown(f"<span class='price'>{money(item['price'])}</span>", unsafe_allow_html=True)

with tab_history:
    st.subheader("🧾 Các đơn đã hoàn tất")
    if not st.session_state.orders:
        st.info("Chưa có đơn nào được chốt trong phiên này.")
    else:
        total_revenue = sum(o["total"] for o in st.session_state.orders)
        a,b,c = st.columns(3)
        a.metric("Số đơn", len(st.session_state.orders))
        b.metric("Doanh thu", money(total_revenue))
        c.metric("Trung bình/đơn", money(total_revenue // len(st.session_state.orders)))
        for i, order in enumerate(reversed(st.session_state.orders), 1):
            with st.expander(f"Đơn #{len(st.session_state.orders)-i+1} · {order['time']} · {order['customer']} · {money(order['total'])}"):
                for row in order["items"]:
                    addons = ", ".join(row["addons"]) if row["addons"] else "Không topping"
                    st.write(f"- {row['name']} × {row['qty']} | {addons} | {row.get('note','')}")
                st.write(f"Tạm tính: {money(order['subtotal'])} · Giảm: {money(order['discount'])}")
                st.write(f"**Tổng: {money(order['total'])}** · Khách đưa: {money(order['paid'])} · Thối: {money(order['change'])}")
        if st.button("⚠️ Xóa lịch sử đơn trong phiên"):
            st.session_state.orders = []
            st.rerun()

st.markdown("---")
st.markdown("<div style='text-align:center;color:#c27b9d;font-weight:700'>Made with ♡ for your little pink tea shop · 🎀</div>", unsafe_allow_html=True)
