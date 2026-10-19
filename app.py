from pathlib import Path
from datetime import datetime, date, timedelta
import os, json, secrets
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Boolean, DateTime, Date, Float, ForeignKey, Text, text

ROOT=Path(__file__).parent; ASSETS=ROOT/'assets'
st.set_page_config(page_title='Bé Dâu | Milk Tea Studio',page_icon='🎀',layout='wide',initial_sidebar_state='expanded')
st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');
:root{--cream:#FFF9F7;--paper:#FFF;--blush:#F7DFE7;--rose:#E8A4BA;--berry:#B74470;--ink:#3E3038;--muted:#8D7882;--line:#F0DCE3}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;color:var(--ink)}.stApp{background:linear-gradient(140deg,#FFF9F7,#FFF4F7 56%,#FFF9F7)}.block-container{max-width:1440px;padding-top:1.2rem}
h1{font-family:'Playfair Display',serif!important;color:#4C3440}.hero{background:linear-gradient(115deg,#F7DFE7,#FFFDFB 72%);border:1px solid #EED1DC;border-radius:24px;padding:24px 28px;box-shadow:0 12px 35px #82304f0e}.eyebrow{color:#B74470;font-size:.72rem;font-weight:700;letter-spacing:.15em;text-transform:uppercase}.muted{color:#8D7882;font-size:.84rem}.panel{background:#fff;border:1px solid #F0DCE3;border-radius:17px;padding:15px}.klabel{color:#8D7882;font-size:.82rem;font-weight:600}.kvalue{font-size:1.5rem;font-weight:700;letter-spacing:-.04em}.price{color:#B74470;font-weight:800}.menu-card{background:#fff;border:1px solid #F0DCE3;border-radius:17px;padding:12px;height:100%}.stButton>button{border-radius:12px;border:1px solid #E8B6C8;color:#963A60;background:#FFF7FA;font-weight:700}.stButton>button:hover{background:#B74470;color:#fff;border-color:#B74470}.stButton>button[kind="primary"]{background:#B74470;color:#fff;border-color:#B74470}[data-testid="stSidebar"]{background:#FFFDFB;border-right:1px solid #F0DCE3}[data-testid="stMetric"]{background:white;border:1px solid #F0DCE3;border-radius:15px;padding:12px}hr{border-color:#F0DCE3}@media(max-width:760px){.block-container{padding-left:1rem;padding-right:1rem}.hero{padding:18px;border-radius:18px}}
</style>''',unsafe_allow_html=True)

url=None
try:url=st.secrets.get('DATABASE_URL')
except Exception: url=os.getenv('DATABASE_URL')
if url:
    if url.startswith('postgres://'): url=url.replace('postgres://','postgresql+psycopg://',1)
    elif url.startswith('postgresql://') and '+psycopg' not in url: url=url.replace('postgresql://','postgresql+psycopg://',1)
    engine=create_engine(url,pool_pre_ping=True,pool_recycle=300); DB_MODE='PostgreSQL'
else: engine=create_engine(f"sqlite:///{ROOT/'be_dau_local.db'}",connect_args={'check_same_thread':False}); DB_MODE='SQLite cục bộ'
md=MetaData()
products=Table('products',md,Column('id',Integer,primary_key=True),Column('name',String(180),nullable=False),Column('category',String(80),nullable=False),Column('price',Integer,nullable=False),Column('active',Boolean,default=True,nullable=False),Column('image',String(180)),Column('description',String(300)),Column('created_at',DateTime,default=datetime.utcnow))
ing=Table('ingredients',md,Column('id',Integer,primary_key=True),Column('name',String(160),nullable=False),Column('unit',String(20),nullable=False),Column('stock',Float,default=0),Column('min_stock',Float,default=0),Column('cost',Float,default=0),Column('expiry',Date))
recipes=Table('recipes',md,Column('id',Integer,primary_key=True),Column('product_id',Integer,ForeignKey('products.id')),Column('ingredient_id',Integer,ForeignKey('ingredients.id')),Column('qty',Float,nullable=False))
customers=Table('customers',md,Column('id',Integer,primary_key=True),Column('name',String(160),nullable=False),Column('phone',String(40),unique=True),Column('points',Integer,default=0),Column('notes',String(500)),Column('created_at',DateTime,default=datetime.utcnow))
orders=Table('orders',md,Column('id',Integer,primary_key=True),Column('code',String(40),unique=True),Column('customer_id',Integer,ForeignKey('customers.id')),Column('customer',String(160)),Column('order_type',String(30)),Column('status',String(30)),Column('subtotal',Integer),Column('discount',Integer),Column('total',Integer),Column('paid',Integer),Column('change_amt',Integer),Column('payment',String(40)),Column('note',String(500)),Column('created_at',DateTime,default=datetime.utcnow))
items=Table('order_items',md,Column('id',Integer,primary_key=True),Column('order_id',Integer,ForeignKey('orders.id')),Column('product_id',Integer,ForeignKey('products.id')),Column('name',String(180)),Column('price',Integer),Column('qty',Integer),Column('size',String(10)),Column('sugar',String(10)),Column('ice',String(30)),Column('toppings',Text),Column('top_cost',Integer),Column('note',String(300)))
movements=Table('stock_movements',md,Column('id',Integer,primary_key=True),Column('ingredient_id',Integer,ForeignKey('ingredients.id')),Column('kind',String(40)),Column('qty',Float),Column('reason',String(300)),Column('created_at',DateTime,default=datetime.utcnow))
expenses=Table('expenses',md,Column('id',Integer,primary_key=True),Column('category',String(80)),Column('amount',Integer),Column('note',String(300)),Column('created_at',DateTime,default=datetime.utcnow))
shifts=Table('shifts',md,Column('id',Integer,primary_key=True),Column('opened',DateTime),Column('closed',DateTime),Column('opening_cash',Integer),Column('closing_cash',Integer),Column('status',String(30)),Column('note',String(300)))
logs=Table('audit_logs',md,Column('id',Integer,primary_key=True),Column('action',String(80)),Column('detail',String(500)),Column('created_at',DateTime,default=datetime.utcnow))
md.create_all(engine)

def allq(sql,p=None):
    with engine.connect() as c:return pd.read_sql(text(sql),c,params=p or {})
def run(sql,p=None):
    with engine.begin() as c:return c.execute(text(sql),p or {})
def log(a,d=''):run('INSERT INTO audit_logs(action,detail,created_at) VALUES(:a,:d,:t)',{'a':a,'d':d[:500],'t':datetime.now()})
def cash(v):return f"{int(round(float(v or 0))):,}đ".replace(',','.')
def img(name):
    p=ASSETS/str(name or '')
    return str(p) if p.exists() else None
def header(title,sub):st.markdown(f'<div class="eyebrow">BÉ DÂU MILK TEA STUDIO</div><h1 style="margin:.2rem 0">{title}</h1><p class="muted">{sub}</p>',unsafe_allow_html=True)
def metric(label,value,note=''):
    st.markdown(f'<div class="panel"><div class="klabel">{label}</div><div class="kvalue">{value}</div><div class="muted">{note}</div></div>',unsafe_allow_html=True)

seed=[('Trà sữa trân châu đường đen','Trà sữa',35000,'trasua_tranchau.png','Béo thơm, trân châu dai'),('Trà sữa truyền thống','Trà sữa',29000,'trasua_truyenthong.png','Vị trà đậm dịu ngọt'),('Trà đào cam sả','Trà trái cây',32000,'tradao.png','Thanh mát, thơm trái cây'),('Trà vải hoa hồng','Trà trái cây',33000,'travai.png','Ngọt nhẹ, thơm dịu'),('Matcha latte','Đá xay & latte',38000,'matcha.png','Matcha thơm, sữa mịn'),('Chocolate đá xay','Đá xay & latte',40000,'chocolate.png','Chocolate đậm vị'),('Sữa tươi trân châu','Trà sữa',36000,'suatuoi.png','Sữa tươi béo thơm'),('Trà chanh mật ong','Trà trái cây',25000,'trachanh.png','Chua ngọt dễ uống')]
with engine.begin() as c:
    if c.execute(text('SELECT COUNT(*) FROM products')).scalar_one()==0:
        c.execute(products.insert(),[dict(name=n,category=cat,price=pr,active=True,image=im,description=desc) for n,cat,pr,im,desc in seed])
    if c.execute(text('SELECT COUNT(*) FROM ingredients')).scalar_one()==0:
        c.execute(ing.insert(),[dict(name=n,unit=u,stock=s,min_stock=m,cost=cost) for n,u,s,m,cost in [('Trà nền','g',2500,500,.08),('Sữa','ml',8000,1500,.035),('Trân châu','g',3500,600,.09),('Đường','g',5000,1000,.02),('Ly nhựa','cái',300,80,450),('Nắp ly','cái',300,80,180),('Đào ngâm','g',2000,400,.11),('Matcha','g',500,100,1.2),('Chocolate','g',700,120,.45),('Chanh','g',1000,200,.12)]])

if 'cart' not in st.session_state:st.session_state.cart=[]
with st.sidebar:
    st.markdown('<div style="font-size:2rem;color:#B74470">◈</div><div style="font-family:Playfair Display,serif;font-size:1.55rem;font-weight:700;color:#84304F">Bé Dâu</div><div style="font-size:.68rem;letter-spacing:.15em;color:#9A7B89">MILK TEA STUDIO</div>',unsafe_allow_html=True)
    st.caption('Không gian quản lý cửa hàng')
    page=st.radio('ĐIỀU HƯỚNG',['Tổng quan','Bán hàng','Đơn hàng','Thực đơn','Kho nguyên liệu','Khách hàng','Chi phí','Ca làm','Báo cáo','Cài đặt & nhật ký'],label_visibility='collapsed')
    st.divider()
    if DB_MODE=='PostgreSQL':st.success('Đã kết nối PostgreSQL')
    else:st.warning('SQLite cục bộ');st.caption('Trên Streamlit Cloud, cấu hình DATABASE_URL để lưu bền vững.')
    st.caption('Rose Luxury · v1.0')

if page=='Tổng quan':
    header('Tổng quan','Một góc nhìn rõ ràng về hoạt động của tiệm.')
    today=date.today().isoformat(); od=allq("SELECT * FROM orders WHERE DATE(created_at)=:d AND status='Đã thanh toán'",{'d':today}); rev=int(od.total.sum()) if not od.empty else 0; count=len(od); low=allq('SELECT * FROM ingredients WHERE stock<=min_stock')
    cs=st.columns(4)
    for col,(lab,val,note) in zip(cs,[('Doanh thu hôm nay',cash(rev),'Đơn đã thanh toán'),('Đơn hàng',str(count),'Trong ngày'),('Trung bình/đơn',cash(rev/count if count else 0),'Giá trị trung bình'),('Cảnh báo kho',str(len(low)),'Nguyên liệu cần xem')]):
        with col:metric(lab,val,note)
    a,b=st.columns([1.3,1],gap='large')
    with a:
        st.markdown('### Doanh thu 7 ngày gần nhất'); tr=allq("SELECT DATE(created_at) ngay,SUM(total) doanh_thu FROM orders WHERE DATE(created_at)>=:s AND status='Đã thanh toán' GROUP BY DATE(created_at) ORDER BY ngay",{'s':(date.today()-timedelta(days=6)).isoformat()})
        if tr.empty:st.info('Biểu đồ sẽ xuất hiện sau khi có đơn hàng thực tế.')
        else:tr['ngay']=pd.to_datetime(tr.ngay);st.line_chart(tr.set_index('ngay').doanh_thu)
    with b:
        st.markdown('### Món bán chạy'); best=allq("SELECT i.name AS 'Tên món',SUM(i.qty) AS 'Số ly' FROM order_items i JOIN orders o ON o.id=i.order_id WHERE o.status='Đã thanh toán' GROUP BY i.name ORDER BY SUM(i.qty) DESC LIMIT 5")
        st.dataframe(best,hide_index=True,use_container_width=True) if not best.empty else st.info('Chưa có dữ liệu bán hàng.')
    st.markdown('### Cảnh báo tồn kho')
    st.dataframe(low[['name','stock','unit','min_stock']].rename(columns={'name':'Nguyên liệu','stock':'Tồn','unit':'Đơn vị','min_stock':'Ngưỡng'}) if not low.empty else pd.DataFrame(columns=['Nguyên liệu','Tồn','Đơn vị','Ngưỡng']),hide_index=True,use_container_width=True)

elif page=='Bán hàng':
    header('Bán hàng','Tạo đơn mới, tùy chỉnh từng ly và chốt thanh toán.')
    p=allq('SELECT * FROM products WHERE active=TRUE ORDER BY category,name')
    if p.empty:st.warning('Chưa có món đang bán. Thêm món tại mục Thực đơn.')
    else:
        c1,c2=st.columns([1.2,1]);
        with c1:search=st.text_input('Tìm món',placeholder='Tên đồ uống...')
        with c2:cat=st.selectbox('Danh mục',['Tất cả']+sorted(p.category.unique().tolist()))
        p=p[p.name.str.contains(search,case=False,na=False)]
        if cat!='Tất cả':p=p[p.category==cat]
        left,right=st.columns([1.2,.9],gap='large')
        with left:
            st.markdown('### Thực đơn'); grid=st.columns(2)
            for ix,r in p.reset_index(drop=True).iterrows():
                with grid[ix%2]:
                    st.markdown('<div class="menu-card">',unsafe_allow_html=True)
                    im=img(r.image)
                    if im:st.image(im,use_container_width=True)
                    st.markdown(f"**{r['name']}**");st.caption(r.description or r.category);st.markdown(f'<div class="price">{cash(r.price)}</div>',unsafe_allow_html=True)
                    qty=st.number_input('Số lượng',1,30,1,key=f'q{r.id}');size=st.selectbox('Size',['S','M','L'],index=1,key=f's{r.id}');sugar=st.selectbox('Đường',['0%','30%','50%','70%','100%'],index=4,key=f'su{r.id}');ice=st.selectbox('Đá',['Không đá','Ít đá','Bình thường'],index=2,key=f'i{r.id}')
                    tp={'Trân châu đen':5000,'Trân châu trắng':7000,'Pudding trứng':7000,'Thạch trái cây':5000,'Kem cheese':10000}; tops=st.multiselect('Topping',list(tp),key=f't{r.id}');note=st.text_input('Ghi chú',placeholder='Ít đá...',key=f'n{r.id}')
                    if st.button('＋ Thêm vào đơn',key=f'a{r.id}',use_container_width=True):
                        st.session_state.cart.append({'product_id':int(r.id),'name':r['name'],'price':max(0,int(r.price)+{'S':-5000,'M':0,'L':7000}[size]),'qty':int(qty),'size':size,'sugar':sugar,'ice':ice,'tops':tops,'top_cost':sum(tp[x] for x in tops),'note':note});st.toast('Đã thêm món vào đơn')
                    st.markdown('</div>',unsafe_allow_html=True)
        with right:
            st.markdown('### Đơn hiện tại'); cart=st.session_state.cart
            if not cart:st.info('Chọn món bên trái để bắt đầu đơn hàng.')
            else:
                for ix,it in enumerate(cart):
                    with st.container(border=True):
                        st.markdown(f"**{it['name']}** · size {it['size']}");st.caption(f"{cash(it['price'])}/ly · {it['sugar']} đường · {it['ice']} · {', '.join(it['tops']) or 'Không topping'}")
                        qx,dx=st.columns([2,1]);
                        with qx:it['qty']=st.number_input('Số lượng',1,50,int(it['qty']),key=f'cq{ix}')
                        with dx:
                            if st.button('Xóa',key=f'del{ix}'):cart.pop(ix);st.rerun()
                        if it.get('note'):st.caption(it['note'])
                subtotal=sum((i['price']+i['top_cost'])*i['qty'] for i in cart);st.write('Tạm tính:',cash(subtotal))
                cdf=allq('SELECT id,name,phone FROM customers ORDER BY name');choices=['Khách lẻ']+[f"{r['name']} · {r['phone'] or 'chưa có SĐT'} · #{r['id']}" for _,r in cdf.iterrows()];choice=st.selectbox('Khách hàng',choices);cid=None;cn='Khách lẻ'
                if choice!='Khách lẻ':cid=int(choice.rsplit('#',1)[1]);cn=cdf[cdf.id==cid].iloc[0]['name']
                typ=st.selectbox('Hình thức',['Mang đi','Dùng tại quán','Giao hàng']);pay=st.selectbox('Thanh toán',['Tiền mặt','Chuyển khoản','Thẻ','Khác']);disc_pct=st.selectbox('Giảm giá (%)',[0,5,10,15,20]);disc=round(subtotal*disc_pct/100);total=subtotal-disc
                st.markdown(f'### Tổng thanh toán: {cash(total)}');paid=st.number_input('Khách đưa (VNĐ)',min_value=0,value=int(total),step=1000);st.caption('Tiền thối: '+cash(max(0,paid-total)));onote=st.text_input('Ghi chú đơn hàng')
                if st.button('Hoàn tất & lưu đơn',type='primary',use_container_width=True):
                    if paid<total:st.error('Số tiền khách đưa chưa đủ.')
                    else:
                        code='BD'+datetime.now().strftime('%y%m%d')+'-'+secrets.token_hex(2).upper()
                        with engine.begin() as conn:
                            oid=conn.execute(orders.insert().values(code=code,customer_id=cid,customer=cn,order_type=typ,status='Đã thanh toán',subtotal=subtotal,discount=disc,total=total,paid=int(paid),change_amt=int(paid)-total,payment=pay,note=onote,created_at=datetime.now())).inserted_primary_key[0]
                            for it in cart:
                                conn.execute(items.insert().values(order_id=oid,product_id=it['product_id'],name=it['name'],price=it['price'],qty=it['qty'],size=it['size'],sugar=it['sugar'],ice=it['ice'],toppings=json.dumps(it['tops'],ensure_ascii=False),top_cost=it['top_cost'],note=it['note']))
                                rr=conn.execute(text('SELECT ingredient_id,qty FROM recipes WHERE product_id=:p'),{'p':it['product_id']}).fetchall()
                                for rec in rr:
                                    amount=float(rec.qty)*it['qty'];conn.execute(text('UPDATE ingredients SET stock=stock-:q WHERE id=:i'),{'q':amount,'i':rec.ingredient_id});conn.execute(movements.insert().values(ingredient_id=rec.ingredient_id,kind='Xuất bán',qty=-amount,reason=f'{code} · {it["name"]}',created_at=datetime.now()))
                            if cid:conn.execute(text('UPDATE customers SET points=points+:p WHERE id=:i'),{'p':total//10000,'i':cid})
                            conn.execute(logs.insert().values(action='Hoàn tất đơn',detail=f'{code} · {cash(total)}',created_at=datetime.now()))
                        st.session_state.cart=[];st.session_state.receipt={'code':code,'customer':cn,'total':total,'sub':subtotal,'disc':disc,'change':int(paid)-total,'time':datetime.now().strftime('%d/%m/%Y %H:%M')};st.success(f'Đã lưu đơn {code}');st.rerun()
            if st.session_state.get('receipt'):
                rec=st.session_state.receipt
                with st.expander('Hóa đơn gần nhất',expanded=True):
                    st.markdown(f"**BÉ DÂU MILK TEA**  \nMã đơn: `{rec['code']}`  \nThời gian: {rec['time']}  \nKhách: {rec['customer']}");st.write('Tạm tính:',cash(rec['sub']));st.write('Giảm giá:',cash(rec['disc']));st.markdown(f"### Tổng: {cash(rec['total'])}");st.write('Tiền thối:',cash(rec['change']))
                    st.download_button('Tải hóa đơn TXT',f"BÉ DÂU MILK TEA\nMã đơn: {rec['code']}\nKhách: {rec['customer']}\nTổng: {cash(rec['total'])}\nTiền thối: {cash(rec['change'])}\n",file_name=f"hoa_don_{rec['code']}.txt")

elif page=='Đơn hàng':
    header('Đơn hàng','Tra cứu, kiểm tra chi tiết và xuất dữ liệu.');a,b,c=st.columns(3)
    with a:start=st.date_input('Từ ngày',date.today()-timedelta(days=30))
    with b:end=st.date_input('Đến ngày',date.today())
    with c:status=st.selectbox('Trạng thái',['Tất cả','Đã thanh toán','Đã hủy','Hoàn tiền'])
    sql="SELECT id,code AS 'Mã đơn',customer AS 'Khách hàng',order_type AS 'Hình thức',status AS 'Trạng thái',subtotal AS 'Tạm tính',discount AS 'Giảm giá',total AS 'Tổng tiền',payment AS 'Thanh toán',created_at AS 'Thời gian' FROM orders WHERE DATE(created_at)>=:s AND DATE(created_at)<=:e";params={'s':start.isoformat(),'e':end.isoformat()}
    if status!='Tất cả':sql+=' AND status=:st';params['st']=status
    df=allq(sql+' ORDER BY created_at DESC',params)
    if df.empty:st.info('Không có đơn hàng trong khoảng thời gian này.')
    else:
        st.dataframe(df,hide_index=True,use_container_width=True);st.download_button('Xuất CSV',df.to_csv(index=False).encode('utf-8-sig'),'don_hang.csv','text/csv');code=st.selectbox('Xem chi tiết đơn',df['Mã đơn'].tolist());detail=allq("SELECT name AS 'Món',qty AS 'SL',size AS 'Size',price AS 'Giá/ly',top_cost AS 'Topping/ly',sugar AS 'Đường',ice AS 'Đá',toppings AS 'Topping',note AS 'Ghi chú' FROM order_items i JOIN orders o ON o.id=i.order_id WHERE o.code=:c",{'c':code});st.dataframe(detail,hide_index=True,use_container_width=True)
        if df[df['Mã đơn']==code].iloc[0]['Trạng thái']!='Đã hủy' and st.button('Đánh dấu đơn là hủy'):
            run("UPDATE orders SET status='Đã hủy' WHERE code=:c",{'c':code});log('Hủy đơn',code);st.warning('Đã hủy trạng thái. Kho không tự hoàn nguyên liệu, hãy kiểm tra và điều chỉnh nếu cần.');st.rerun()

elif page=='Thực đơn':
    header('Thực đơn','Quản lý món, giá bán và trạng thái hiển thị.');df=allq('SELECT * FROM products ORDER BY category,name');a,b=st.columns([1.1,1]);
    with a:st.dataframe(df[['id','name','category','price','active','description']].rename(columns={'id':'ID','name':'Tên món','category':'Danh mục','price':'Giá','active':'Đang bán','description':'Mô tả'}),hide_index=True,use_container_width=True);st.download_button('Xuất menu CSV',df.to_csv(index=False).encode('utf-8-sig'),'menu.csv','text/csv')
    with b:
        st.markdown('### Thêm món');
        with st.form('newprod',clear_on_submit=True):
            n=st.text_input('Tên món');cat=st.selectbox('Danh mục',['Trà sữa','Trà trái cây','Đá xay & latte','Cà phê','Khác']);price=st.number_input('Giá bán',min_value=0,value=30000,step=1000);im=st.selectbox('Ảnh',['trasua_tranchau.png','trasua_truyenthong.png','tradao.png','travai.png','matcha.png','chocolate.png','suatuoi.png','trachanh.png']);desc=st.text_input('Mô tả');ok=st.form_submit_button('Thêm món',type='primary')
            if ok:
                if not n.strip():st.error('Nhập tên món.')
                else:run('INSERT INTO products(name,category,price,active,image,description,created_at) VALUES(:n,:c,:p,TRUE,:i,:d,:t)',{'n':n,'c':cat,'p':int(price),'i':im,'d':desc,'t':datetime.now()});log('Thêm món',n);st.success('Đã thêm.');st.rerun()
        st.markdown('### Chỉnh sửa món');pid=st.selectbox('Chọn món',df.id.tolist(),format_func=lambda x:df[df.id==x].iloc[0]['name']);r=df[df.id==pid].iloc[0]
        with st.form('editprod'):
            en=st.text_input('Tên',r['name']);ec=st.text_input('Danh mục',r['category']);ep=st.number_input('Giá',min_value=0,value=int(r.price),step=1000);ed=st.text_input('Mô tả',r.description or '');ea=st.checkbox('Đang kinh doanh',bool(r.active));save=st.form_submit_button('Lưu thay đổi')
            if save:run('UPDATE products SET name=:n,category=:c,price=:p,description=:d,active=:a WHERE id=:i',{'n':en,'c':ec,'p':int(ep),'d':ed,'a':ea,'i':int(pid)});log('Sửa món',en);st.success('Đã cập nhật.');st.rerun()

elif page=='Kho nguyên liệu':
    header('Kho nguyên liệu','Theo dõi tồn kho, nhập xuất và công thức định lượng.');df=allq('SELECT * FROM ingredients ORDER BY name');low=df[df.stock<=df.min_stock] if not df.empty else df
    a,b,c=st.columns(3)
    with a:metric('Nguyên liệu',str(len(df)),'Đang theo dõi')
    with b:metric('Dưới ngưỡng',str(len(low)),'Cần kiểm tra')
    with c:metric('Giá trị tồn ước tính',cash((df.stock*df.cost).sum() if not df.empty else 0),'Theo giá nhập đã khai báo')
    st.dataframe(df.rename(columns={'id':'ID','name':'Nguyên liệu','unit':'Đơn vị','stock':'Tồn','min_stock':'Ngưỡng thấp','cost':'Giá/đơn vị','expiry':'Hạn dùng'}),hide_index=True,use_container_width=True)
    left,right=st.columns(2)
    with left:
        st.markdown('### Thêm nguyên liệu')
        with st.form('newing'):
            n=st.text_input('Tên nguyên liệu');u=st.selectbox('Đơn vị',['g','ml','cái','kg','lít','gói']);s=st.number_input('Tồn ban đầu',min_value=0.0);m=st.number_input('Ngưỡng cảnh báo',min_value=0.0);cost=st.number_input('Giá nhập mỗi đơn vị',min_value=0.0);ex=st.date_input('Hạn dùng',value=None);ok=st.form_submit_button('Thêm nguyên liệu',type='primary')
            if ok:
                if not n.strip():st.error('Nhập tên nguyên liệu.')
                else:run('INSERT INTO ingredients(name,unit,stock,min_stock,cost,expiry) VALUES(:n,:u,:s,:m,:c,:e)',{'n':n,'u':u,'s':s,'m':m,'c':cost,'e':ex});log('Thêm nguyên liệu',n);st.success('Đã thêm.');st.rerun()
    with right:
        st.markdown('### Nhập / điều chỉnh kho')
        if not df.empty:
            iid=st.selectbox('Nguyên liệu',df.id.tolist(),format_func=lambda x:df[df.id==x].iloc[0]['name']);kind=st.radio('Loại',['Nhập kho','Xuất hao hụt','Điều chỉnh tăng','Điều chỉnh giảm'],horizontal=True);amount=st.number_input('Số lượng',min_value=0.0);reason=st.text_input('Lý do')
            if st.button('Lưu biến động kho',type='primary'):
                old=float(df[df.id==iid].iloc[0].stock);sign=1 if kind in ['Nhập kho','Điều chỉnh tăng'] else -1
                if sign<0 and amount>old:st.error('Số lượng xuất vượt tồn.')
                else:run('UPDATE ingredients SET stock=stock+:q WHERE id=:i',{'q':sign*amount,'i':int(iid)});run('INSERT INTO stock_movements(ingredient_id,kind,qty,reason,created_at) VALUES(:i,:k,:q,:r,:t)',{'i':int(iid),'k':kind,'q':sign*amount,'r':reason,'t':datetime.now()});log('Điều chỉnh kho',f'{kind} {amount} {reason}');st.success('Đã cập nhật.');st.rerun()
    p=allq('SELECT id,name FROM products ORDER BY name');df=allq('SELECT id,name,unit FROM ingredients ORDER BY name')
    if not p.empty and not df.empty:
        st.markdown('### Công thức nguyên liệu');
        with st.form('recipe'):
            pid=st.selectbox('Món',p.id.tolist(),format_func=lambda x:p[p.id==x].iloc[0]['name']);iid=st.selectbox('Nguyên liệu',df.id.tolist(),format_func=lambda x:df[df.id==x].iloc[0]['name']);qty=st.number_input('Lượng dùng cho một ly',min_value=0.0);ok=st.form_submit_button('Lưu công thức')
            if ok:
                old=allq('SELECT id FROM recipes WHERE product_id=:p AND ingredient_id=:i',{'p':int(pid),'i':int(iid)})
                if old.empty:run('INSERT INTO recipes(product_id,ingredient_id,qty) VALUES(:p,:i,:q)',{'p':int(pid),'i':int(iid),'q':qty})
                else:run('UPDATE recipes SET qty=:q WHERE product_id=:p AND ingredient_id=:i',{'p':int(pid),'i':int(iid),'q':qty})
                log('Lưu công thức',f'món {pid}, nguyên liệu {iid}, {qty}');st.success('Đã lưu công thức.');st.rerun()
        rec=allq("SELECT p.name AS 'Món',i.name AS 'Nguyên liệu',r.qty AS 'Lượng/ly',i.unit AS 'Đơn vị' FROM recipes r JOIN products p ON p.id=r.product_id JOIN ingredients i ON i.id=r.ingredient_id ORDER BY p.name")
        if not rec.empty:st.dataframe(rec,hide_index=True,use_container_width=True)
    st.info('Dữ liệu tồn kho ban đầu là mẫu. Hãy kiểm kê và khai báo đúng công thức trước khi dùng tự động trừ kho.')

elif page=='Khách hàng':
    header('Khách hàng','Quản lý khách quen và chương trình tích điểm.');a,b=st.columns(2)
    with a:
        with st.form('customer',clear_on_submit=True):
            n=st.text_input('Tên khách');phone=st.text_input('Số điện thoại (không bắt buộc)');note=st.text_area('Ghi chú');ok=st.form_submit_button('Lưu khách',type='primary')
            if ok:
                if not n.strip():st.error('Nhập tên khách.')
                else:
                    try:run('INSERT INTO customers(name,phone,points,notes,created_at) VALUES(:n,:p,0,:no,:t)',{'n':n,'p':phone.strip() or None,'no':note,'t':datetime.now()});log('Thêm khách',n);st.success('Đã lưu.');st.rerun()
                    except Exception:st.error('Số điện thoại đã tồn tại hoặc dữ liệu không hợp lệ.')
    with b:
        search=st.text_input('Tìm khách theo tên hoặc số điện thoại');df=allq('SELECT id,name,phone,points,notes FROM customers ORDER BY name')
        if search:df=df[df.apply(lambda r:search.lower() in str(r['name']).lower() or search.lower() in str(r['phone'] or '').lower(),axis=1)]
        st.dataframe(df.rename(columns={'id':'ID','name':'Tên','phone':'Điện thoại','points':'Điểm','notes':'Ghi chú'}),hide_index=True,use_container_width=True)
    st.caption('Quy tắc mẫu: 1 điểm / 10.000đ. Đổi điểm tự động chưa được triển khai.')

elif page=='Chi phí':
    header('Chi phí','Ghi nhận khoản chi để theo dõi hiệu quả kinh doanh.')
    with st.form('expense',clear_on_submit=True):
        a,b=st.columns(2)
        with a:cat=st.selectbox('Danh mục',['Nguyên liệu','Mặt bằng','Điện nước','Lương','Bao bì','Marketing','Vận chuyển','Khác'])
        with b:amount=st.number_input('Số tiền',min_value=0,value=0,step=1000)
        note=st.text_input('Nội dung');ok=st.form_submit_button('Ghi nhận chi phí',type='primary')
        if ok:
            if amount<=0:st.error('Số tiền phải lớn hơn 0.')
            else:run('INSERT INTO expenses(category,amount,note,created_at) VALUES(:c,:a,:n,:t)',{'c':cat,'a':int(amount),'n':note,'t':datetime.now()});log('Ghi chi phí',f'{cat} {cash(amount)}');st.success('Đã lưu.');st.rerun()
    df=allq("SELECT category AS 'Danh mục',amount AS 'Số tiền',note AS 'Nội dung',created_at AS 'Thời gian' FROM expenses ORDER BY created_at DESC")
    if not df.empty:st.metric('Tổng chi phí đã ghi nhận',cash(df['Số tiền'].sum()));st.dataframe(df,hide_index=True,use_container_width=True);st.download_button('Xuất CSV',df.to_csv(index=False).encode('utf-8-sig'),'chi_phi.csv','text/csv')
    else:st.info('Chưa có khoản chi.')

elif page=='Ca làm':
    header('Ca làm','Mở ca, đối chiếu tiền mặt và chốt ca.');active=allq("SELECT * FROM shifts WHERE status='Đang mở' ORDER BY opened DESC LIMIT 1")
    if active.empty:
        with st.form('open_shift'):
            opening=st.number_input('Tiền mặt đầu ca',min_value=0,value=0,step=10000);note=st.text_input('Ghi chú');ok=st.form_submit_button('Mở ca',type='primary')
            if ok:run("INSERT INTO shifts(opened,opening_cash,status,note) VALUES(:t,:c,'Đang mở',:n)",{'t':datetime.now(),'c':int(opening),'n':note});log('Mở ca',cash(opening));st.success('Đã mở ca.');st.rerun()
    else:
        sh=active.iloc[0];cashsales=allq("SELECT COALESCE(SUM(total),0) rev FROM orders WHERE created_at>=:t AND status='Đã thanh toán' AND payment='Tiền mặt'",{'t':sh.opened});expected=int(sh.opening_cash)+int(cashsales.iloc[0].rev or 0);st.success(f"Đang mở ca từ {sh.opened}. Tiền mặt dự kiến: {cash(expected)}")
        with st.form('close_shift'):
            closing=st.number_input('Tiền mặt thực đếm',min_value=0,value=expected,step=10000);note=st.text_input('Ghi chú kết ca');ok=st.form_submit_button('Chốt ca',type='primary')
            if ok:run("UPDATE shifts SET closed=:t,closing_cash=:c,status='Đã đóng',note=:n WHERE id=:i",{'t':datetime.now(),'c':int(closing),'n':note,'i':int(sh.id)});log('Chốt ca',f'chênh lệch {cash(closing-expected)}');st.success(f'Đã chốt ca. Chênh lệch: {cash(closing-expected)}');st.rerun()
    df=allq("SELECT id AS 'Ca',opened AS 'Mở lúc',closed AS 'Đóng lúc',opening_cash AS 'Tiền đầu ca',closing_cash AS 'Tiền cuối ca',status AS 'Trạng thái' FROM shifts ORDER BY opened DESC LIMIT 20");st.dataframe(df,hide_index=True,use_container_width=True)

elif page=='Báo cáo':
    header('Báo cáo','Doanh thu, chi phí và hiệu suất món theo khoảng ngày.');a,b=st.columns(2)
    with a:start=st.date_input('Từ ngày',date.today()-timedelta(days=30),key='rs')
    with b:end=st.date_input('Đến ngày',date.today(),key='re')
    par={'s':start.isoformat(),'e':end.isoformat()};sales=allq("SELECT * FROM orders WHERE DATE(created_at)>=:s AND DATE(created_at)<=:e AND status='Đã thanh toán'",par);ex=allq('SELECT * FROM expenses WHERE DATE(created_at)>=:s AND DATE(created_at)<=:e',par);rev=int(sales.total.sum()) if not sales.empty else 0;cost=int(ex.amount.sum()) if not ex.empty else 0
    cs=st.columns(4)
    for col,(lab,val,note) in zip(cs,[('Doanh thu',cash(rev),'Đơn đã thanh toán'),('Số đơn',str(len(sales)),'Trong kỳ'),('Chi phí ghi nhận',cash(cost),'Đã nhập'),('Chênh lệch tạm tính',cash(rev-cost),'Chưa trừ đủ giá vốn')]):
        with col:metric(lab,val,note)
    if not sales.empty:
        sales['ngày']=pd.to_datetime(sales.created_at).dt.date.astype(str);daily=sales.groupby('ngày',as_index=False).total.sum();st.markdown('### Doanh thu theo ngày');st.bar_chart(daily.set_index('ngày').total);st.markdown('### Phương thức thanh toán');st.dataframe(sales.groupby('payment',as_index=False).total.sum().rename(columns={'payment':'Phương thức','total':'Doanh thu'}),hide_index=True,use_container_width=True)
        best=allq("SELECT i.name AS 'Món',SUM(i.qty) AS 'Số lượng',SUM((i.price+i.top_cost)*i.qty) AS 'Doanh thu gộp' FROM order_items i JOIN orders o ON o.id=i.order_id WHERE DATE(o.created_at)>=:s AND DATE(o.created_at)<=:e AND o.status='Đã thanh toán' GROUP BY i.name ORDER BY SUM(i.qty) DESC",par);st.markdown('### Hiệu suất món');st.dataframe(best,hide_index=True,use_container_width=True);st.download_button('Tải đơn hàng CSV',sales.to_csv(index=False).encode('utf-8-sig'),'bao_cao.csv','text/csv')
    else:st.info('Chưa có đơn trong khoảng ngày này.')

else:
    header('Cài đặt & nhật ký','Kiểm tra trạng thái lưu trữ, giới hạn và lịch sử thao tác.');st.markdown('### Trạng thái cơ sở dữ liệu')
    if DB_MODE=='PostgreSQL':st.success('Đang dùng PostgreSQL qua DATABASE_URL.')
    else:st.warning('Đang dùng SQLite cục bộ. Trên Streamlit Cloud, SQLite có thể mất dữ liệu sau khi khởi động lại hoặc triển khai lại.')
    st.markdown('### Tích hợp chưa cấu hình');st.info('Thanh toán online, QR động, SMS, AI, máy in trực tiếp và tài khoản/phân quyền nhân viên chưa được tích hợp. Trường phương thức thanh toán chỉ ghi nhận lựa chọn, không tự chuyển tiền.')
    st.markdown('### Quy tắc cần kiểm tra');st.write('- Giá size mẫu: S giảm 5.000đ, M giữ giá, L tăng 7.000đ.');st.write('- Tích điểm mẫu: 1 điểm / 10.000đ; chưa có quy đổi điểm tự động.');st.write('- Tồn kho tự trừ khi công thức món đã khai báo. Hủy đơn chưa tự hoàn nguyên liệu.');st.write('- Nguyên liệu khởi tạo chỉ là dữ liệu mẫu, hãy kiểm kê trước khi dùng thật.')
    df=allq("SELECT action AS 'Hành động',detail AS 'Chi tiết',created_at AS 'Thời gian' FROM audit_logs ORDER BY created_at DESC LIMIT 100");st.markdown('### Nhật ký gần đây');st.dataframe(df,hide_index=True,use_container_width=True)
    table=st.selectbox('Bảng dữ liệu để xuất CSV',['products','ingredients','recipes','customers','orders','order_items','stock_movements','expenses','shifts','audit_logs']);df=allq(f'SELECT * FROM {table}');st.download_button('Tải CSV sao lưu',df.to_csv(index=False).encode('utf-8-sig'),f'sao_luu_{table}.csv','text/csv')

st.markdown('---');st.markdown('<div style="text-align:center;color:#9B7D89;font-size:.8rem">BÉ DÂU MILK TEA STUDIO · Rose Luxury POS · Built for thoughtful service</div>',unsafe_allow_html=True)
