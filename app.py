# ==========================================
# LINE AI 客服管理中心
# 集中管理所有客戶的 LINE AI 客服機器人
# ==========================================

from flask import Flask, request, jsonify, render_template_string, make_response, redirect
import requests as http_requests
import os
import json
import uuid
from datetime import datetime, date
from concurrent.futures import ThreadPoolExecutor
import sys

app = Flask(__name__)
app.logger.setLevel("INFO")
app.logger.addHandler(logging_handler := __import__('logging').StreamHandler(sys.stdout))
logging_handler.setLevel("INFO")

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
DATA_FILE = "/data/dashboard.json"

# ==========================================
# 資料層
# ==========================================

def _load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"clients": {}, "templates": {}, "settings": {"dashboard_title": "LINE AI 客服管理中心"}}


def _save_data(data):
    try:
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[DATA] Save error: {e}", flush=True)
        return False


def get_all_clients():
    data = _load_data()
    clients = list(data.get("clients", {}).values())
    clients.sort(key=lambda c: c.get("created_at", ""), reverse=True)
    return clients


def get_client(client_id):
    data = _load_data()
    return data.get("clients", {}).get(client_id)


def save_client(client):
    data = _load_data()
    client["updated_at"] = datetime.now().isoformat()
    data.setdefault("clients", {})[client["id"]] = client
    _save_data(data)


def delete_client(client_id):
    data = _load_data()
    data.get("clients", {}).pop(client_id, None)
    _save_data(data)


def get_all_templates():
    data = _load_data()
    return list(data.get("templates", {}).values())


def get_template(template_id):
    data = _load_data()
    return data.get("templates", {}).get(template_id)


def save_template(template):
    data = _load_data()
    template["updated_at"] = datetime.now().isoformat()
    data.setdefault("templates", {})[template["id"]] = template
    _save_data(data)


def delete_template(template_id):
    data = _load_data()
    data.get("templates", {}).pop(template_id, None)
    _save_data(data)


def init_default_templates():
    data = _load_data()
    if data.get("templates"):
        return
    defaults = [
        {
            "id": str(uuid.uuid4()),
            "name": "房地產銷售",
            "industry": "real_estate",
            "description": "適用於建案銷售、房仲門市",
            "system_prompt": """你是「小美」，{品牌名稱}的專業銷售顧問AI。語氣親切專業。

【物件資訊】
名稱：{品牌名稱}
地址：{請填入地址}

【產品與價格】
{請填入房型、價格、坪數等資訊}

【地段優勢】
{請填入周邊機能}

【賞屋聯絡】
專線：{請填入電話}
預約制賞屋

【回覆原則】
1. 每次回覆結尾自然引導預約看屋
2. 終極目標：引導客人留下姓名和電話
3. 不確定的問題說「讓我幫您轉接專員確認，請問方便留下姓名和電話嗎？」
4. 回覆簡潔，引導客人繼續聊""",
            "trigger_words": ["找真人", "找人工", "找客服", "預約看屋", "我要看房", "我想了解"],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "餐飲業客服",
            "industry": "restaurant",
            "description": "適用於餐廳、咖啡廳、飲料店",
            "system_prompt": """你是「小食」，{品牌名稱}的專業客服AI。語氣親切活潑。

【餐廳資訊】
名稱：{品牌名稱}
地址：{請填入地址}
營業時間：{請填入營業時間}

【菜單亮點】
{請填入招牌菜色、價位範圍}

【服務項目】
{內用/外帶/外送/包場/訂位}

【聯絡方式】
電話：{請填入電話}
訂位方式：{請填入訂位方式}

【回覆原則】
1. 回覆結尾自然引導訂位或到店消費
2. 推薦餐點時展現熱情
3. 不確定的問題說「讓我幫您確認一下，請問方便留下姓名和電話嗎？」
4. 回覆簡潔有趣""",
            "trigger_words": ["找真人", "找人工", "找客服", "訂位", "預約", "包場"],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "美業客服",
            "industry": "beauty",
            "description": "適用於美髮、美甲、美容、SPA",
            "system_prompt": """你是「小美」，{品牌名稱}的專業客服AI。語氣溫柔專業。

【店家資訊】
名稱：{品牌名稱}
地址：{請填入地址}
營業時間：{請填入營業時間}

【服務項目與價格】
{請填入服務項目、價格}

【設計師/美容師】
{請填入團隊介紹}

【預約方式】
電話：{請填入電話}
{其他預約管道}

【回覆原則】
1. 回覆結尾自然引導預約服務
2. 針對客人需求推薦適合的服務項目
3. 不確定的問題說「讓我幫您轉接專人確認，請問方便留下姓名和電話嗎？」
4. 回覆溫暖專業""",
            "trigger_words": ["找真人", "找人工", "找客服", "預約", "我要預約", "找設計師"],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    ]
    data["templates"] = {t["id"]: t for t in defaults}
    _save_data(data)


init_default_templates()

# ==========================================
# 健康檢查
# ==========================================

def check_single_health(client):
    try:
        r = http_requests.get(client["bot_url"], timeout=5)
        return client["id"], r.status_code == 200
    except Exception:
        return client["id"], False


def check_all_health():
    clients = get_all_clients()
    if not clients:
        return {}
    results = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(check_single_health, c) for c in clients if c.get("bot_url")]
        for f in futures:
            cid, ok = f.result()
            results[cid] = ok
    data = _load_data()
    now = datetime.now().isoformat()
    for cid, ok in results.items():
        if cid in data.get("clients", {}):
            data["clients"][cid]["last_health_check"] = now
            data["clients"][cid]["last_health_ok"] = ok
    _save_data(data)
    return results


# ==========================================
# 認證
# ==========================================

def is_authenticated():
    return request.cookies.get("admin_auth") == ADMIN_PASSWORD


INDUSTRY_LABELS = {
    "real_estate": "房地產",
    "restaurant": "餐飲",
    "beauty": "美業",
    "medical": "醫療",
    "retail": "零售",
    "education": "教育",
    "other": "其他"
}

PLAN_LABELS = {
    "basic": "基本方案",
    "standard": "標準方案",
    "premium": "進階方案"
}

PAYMENT_LABELS = {
    "paid": "已付款",
    "pending": "待付款",
    "overdue": "逾期",
    "trial": "試用中"
}

# ==========================================
# 共用 CSS
# ==========================================

COMMON_CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,sans-serif;background:#f7f5f2;color:#2d1f14}
a{color:#c8401a;text-decoration:none}
.topbar{background:#f0ebe3;border-bottom:0.5px solid #e0d8ce;padding:16px 22px;display:flex;align-items:center;justify-content:space-between}
.topbar-brand{display:flex;align-items:center;gap:12px}
.topbar-logo{width:32px;height:32px;background:#c8401a;border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;color:#fff}
.topbar-name{font-size:15px;font-weight:600;color:#2d1f14}
.topbar-sub{font-size:11px;color:#b0a090;margin-top:2px}
.topbar-right{display:flex;align-items:center;gap:14px}
.topbar-right a{font-size:12px;color:#b0a090}
.topbar-right a:hover{color:#c8401a}
.tabs{display:flex;background:#f0ebe3;border-bottom:0.5px solid #e0d8ce;padding:0 20px;overflow-x:auto}
.tab{padding:10px 16px;font-size:13px;font-weight:500;color:#b0a090;text-decoration:none;border-bottom:2px solid transparent;white-space:nowrap}
.tab.active{color:#c8401a;border-bottom:2px solid #c8401a;font-weight:600}
.tab:hover{color:#2d1f14}
.main{padding:18px 20px 24px;max-width:960px;margin:0 auto}
.stats{display:flex;gap:10px;padding:0 0 14px}
.stat{background:#fff;border-radius:10px;padding:14px 16px;flex:1;border:0.5px solid #e8e2d8}
.stat-n{font-size:26px;font-weight:600;color:#2d1f14}
.stat-n.orange{color:#c8401a}
.stat-n.green{color:#3b6d11}
.stat-n.red{color:#d32f2f}
.stat-l{font-size:11px;color:#b0a090;margin-top:2px}
.card{background:#fff;border-radius:10px;padding:14px 16px;margin-bottom:10px;border:0.5px solid #e8e2d8}
.card-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:8px}
.card-title{font-size:14px;font-weight:600;color:#2d1f14}
.alert{background:#fff0ec;border:0.5px solid #f0c8b0;border-radius:8px;padding:11px 14px;margin-bottom:14px;display:flex;align-items:center;gap:10px}
.alert-dot{width:8px;height:8px;border-radius:50%;background:#d32f2f;flex-shrink:0;animation:blink 1.5s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:0.3}}
.alert-txt{font-size:12px;color:#8b3a1a}
.dot{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:6px}
.dot-green{background:#6abf69}
.dot-red{background:#d32f2f;animation:blink 1.5s infinite}
.dot-grey{background:#ccc}
.badge{font-size:10px;padding:2px 8px;border-radius:8px;font-weight:500;display:inline-block}
.badge-green{background:#d4e8d0;color:#27500a}
.badge-orange{background:#fde8d0;color:#8b5a1a}
.badge-red{background:#f5d5c8;color:#712b13}
.badge-blue{background:#d0e0f0;color:#1a3a6b}
.badge-grey{background:#e8e2d8;color:#6b6050}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px}
.client-card{background:#fff;border-radius:10px;padding:16px;border:0.5px solid #e8e2d8;cursor:pointer;transition:0.15s}
.client-card:hover{border-color:#c8401a;box-shadow:0 2px 8px rgba(200,64,26,0.08)}
.client-card-top{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px}
.client-card-name{font-size:14px;font-weight:600}
.client-card-info{font-size:12px;color:#b0a090;margin-bottom:4px}
.client-card-btns{display:flex;gap:6px;margin-top:10px}
.btn{border:0.5px solid;border-radius:6px;padding:6px 14px;font-size:12px;font-weight:500;cursor:pointer;transition:0.15s;text-decoration:none;display:inline-block;text-align:center}
.btn-primary{background:#c8401a;color:#fff;border-color:#c8401a}
.btn-primary:hover{background:#a83515}
.btn-outline{background:#fff;color:#c8401a;border-color:#e8c0b0}
.btn-outline:hover{background:#fff8f4}
.btn-danger{background:#fff0ec;color:#d32f2f;border-color:#f0c8b0}
.btn-danger:hover{background:#f5d5c8}
.btn-sm{padding:4px 10px;font-size:11px}
.form-group{margin-bottom:14px}
.form-group label{display:block;font-size:12px;font-weight:600;color:#2d1f14;margin-bottom:4px}
.form-group input,.form-group select,.form-group textarea{width:100%;padding:8px 12px;border:0.5px solid #e0d8ce;border-radius:6px;font-size:13px;background:#f7f5f2;color:#2d1f14;font-family:-apple-system,sans-serif}
.form-group textarea{resize:vertical;line-height:1.6}
.form-group input:focus,.form-group select:focus,.form-group textarea:focus{outline:none;border-color:#c8401a}
.form-row{display:flex;gap:14px}
.form-row .form-group{flex:1}
.table-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;padding:8px 10px;font-size:11px;font-weight:600;color:#b0a090;border-bottom:0.5px solid #e8e2d8}
td{padding:10px;border-bottom:0.5px solid #f0ebe3}
tr:hover{background:#faf8f5}
.empty{text-align:center;padding:40px;color:#c8b8a8;font-size:14px}
.login-wrap{display:flex;align-items:center;justify-content:center;min-height:100vh;background:#f7f5f2}
.login-box{background:#fff;border-radius:12px;padding:32px;width:300px;border:0.5px solid #e8e2d8;text-align:center}
.login-logo{width:48px;height:48px;background:#c8401a;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700;color:#fff;margin:0 auto 16px}
.login-box h2{font-size:16px;font-weight:600;margin-bottom:20px;color:#2d1f14}
.login-box input{width:100%;padding:10px 14px;border:0.5px solid #e0d8ce;border-radius:6px;font-size:14px;margin-bottom:12px;text-align:center;background:#f7f5f2}
.login-box button{width:100%;padding:10px;background:#c8401a;color:#fff;border:none;border-radius:6px;font-size:14px;font-weight:600;cursor:pointer}
.err{color:#c8401a;font-size:12px;margin-top:8px}
.toast{position:fixed;bottom:20px;right:20px;background:#2d1f14;color:#f5ede0;padding:10px 18px;border-radius:6px;font-size:13px;display:none;z-index:999}
.sec-title{font-size:13px;font-weight:600;color:#2d1f14;margin:18px 0 10px}
.back-link{font-size:12px;color:#b0a090;margin-bottom:14px;display:inline-block}
.back-link:hover{color:#c8401a}
@media(max-width:600px){.stats{flex-wrap:wrap}.stats .stat{min-width:45%}.form-row{flex-direction:column}.grid{grid-template-columns:1fr}}
"""

# ==========================================
# HTML 模板
# ==========================================

def render_page(title, active_tab, content, extra_js=""):
    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} - LINE AI 管理中心</title>
<style>{COMMON_CSS}</style>
</head>
<body>
<div class="topbar">
  <div class="topbar-brand">
    <div class="topbar-logo">MGR</div>
    <div>
      <div class="topbar-name">LINE AI 管理中心</div>
      <div class="topbar-sub">客服機器人集中管理</div>
    </div>
  </div>
  <div class="topbar-right">
    <a href="/logout">登出</a>
  </div>
</div>
<div class="tabs">
  <a href="/dashboard" class="tab {'active' if active_tab=='overview' else ''}">總覽</a>
  <a href="/dashboard/clients" class="tab {'active' if active_tab=='clients' else ''}">客戶管理</a>
  <a href="/dashboard/billing" class="tab {'active' if active_tab=='billing' else ''}">帳務</a>
  <a href="/dashboard/templates" class="tab {'active' if active_tab=='templates' else ''}">模板庫</a>
</div>
<div class="main">
{content}
</div>
<div class="toast" id="toast"></div>
<script>
function showToast(msg){{const t=document.getElementById('toast');t.textContent=msg;t.style.display='block';setTimeout(()=>t.style.display='none',2000)}}
{extra_js}
</script>
</body>
</html>"""


LOGIN_HTML = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>管理中心登入</title>
<style>{COMMON_CSS}</style>
</head>
<body>
<div class="login-wrap">
  <div class="login-box">
    <div class="login-logo">MGR</div>
    <h2>管理中心登入</h2>
    <form method="POST" action="/login">
      <input type="password" name="password" placeholder="請輸入密碼" required>
      <button type="submit">登入</button>
    </form>
    {{{{ error_html }}}}
  </div>
</div>
</body>
</html>"""


# ==========================================
# 路由 - 認證
# ==========================================

@app.route("/")
def health():
    return "LINE AI 管理中心運作中"


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            resp = make_response(redirect("/dashboard"))
            resp.set_cookie("admin_auth", ADMIN_PASSWORD, max_age=86400 * 7)
            return resp
        error_html = '<p class="err">密碼錯誤</p>'
    else:
        error_html = ""
    html = LOGIN_HTML.replace("{{ error_html }}", error_html)
    resp = make_response(html)
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    return resp


@app.route("/logout")
def logout():
    resp = make_response(redirect("/login"))
    resp.delete_cookie("admin_auth")
    return resp


# ==========================================
# 路由 - 總覽
# ==========================================

@app.route("/dashboard")
def dashboard():
    if not is_authenticated():
        return redirect("/login")
    clients = get_all_clients()
    total = len(clients)
    online = sum(1 for c in clients if c.get("last_health_ok"))
    offline = sum(1 for c in clients if c.get("last_health_check") and not c.get("last_health_ok"))
    today = date.today().isoformat()
    expiring = sum(1 for c in clients if c.get("billing", {}).get("expiry_date", "") and c["billing"]["expiry_date"] <= (date.today().replace(day=date.today().day + 14).isoformat() if date.today().day <= 17 else "9999-12-31") and c["billing"].get("payment_status") != "paid")

    offline_names = [c["brand_name"] for c in clients if c.get("last_health_check") and not c.get("last_health_ok")]
    alert_html = ""
    if offline_names:
        alert_html = f'<div class="alert"><div class="alert-dot"></div><div class="alert-txt">{len(offline_names)} 個機器人離線中：{", ".join(offline_names)}</div></div>'

    cards_html = ""
    if clients:
        cards_html = '<div class="grid">'
        for c in clients:
            health_ok = c.get("last_health_ok")
            checked = c.get("last_health_check")
            if checked:
                dot = "dot-green" if health_ok else "dot-red"
                status_text = "運作中" if health_ok else "離線"
            else:
                dot = "dot-grey"
                status_text = "未檢查"
            plan = PLAN_LABELS.get(c.get("billing", {}).get("plan", ""), c.get("billing", {}).get("plan", ""))
            industry = INDUSTRY_LABELS.get(c.get("industry", ""), c.get("industry", "其他"))
            cards_html += f'''
            <div class="client-card" onclick="location.href='/dashboard/clients/{c["id"]}'">
              <div class="client-card-top">
                <div class="client-card-name"><span class="dot {dot}"></span>{c["brand_name"]}</div>
                <span class="badge badge-grey">{industry}</span>
              </div>
              <div class="client-card-info">狀態：{status_text}</div>
              <div class="client-card-info">聯絡人：{c.get("contact_person", "-")}</div>
              <div class="client-card-info">方案：{plan}</div>
              <div class="client-card-btns">
                <a href="{c.get('admin_url', '#')}" target="_blank" class="btn btn-outline btn-sm" onclick="event.stopPropagation()">開啟後台</a>
                <a href="/dashboard/clients/{c['id']}" class="btn btn-primary btn-sm" onclick="event.stopPropagation()">詳情</a>
              </div>
            </div>'''
        cards_html += '</div>'
    else:
        cards_html = '<div class="empty">還沒有客戶，<a href="/dashboard/clients/new">新增第一個客戶</a></div>'

    content = f"""
    <div class="stats">
      <div class="stat"><div class="stat-n">{total}</div><div class="stat-l">總客戶數</div></div>
      <div class="stat"><div class="stat-n green">{online}</div><div class="stat-l">上線中</div></div>
      <div class="stat"><div class="stat-n red">{offline}</div><div class="stat-l">離線</div></div>
      <div class="stat"><div class="stat-n orange">{expiring}</div><div class="stat-l">即將到期</div></div>
    </div>
    {alert_html}
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
      <div class="sec-title" style="margin:0">所有客戶</div>
      <div style="display:flex;gap:8px">
        <button class="btn btn-outline btn-sm" onclick="checkHealth()">檢查健康狀態</button>
        <a href="/dashboard/clients/new" class="btn btn-primary btn-sm">新增客戶</a>
      </div>
    </div>
    {cards_html}
    """

    js = """
function checkHealth(){
  showToast('正在檢查所有機器人...');
  fetch('/api/health-check',{method:'POST'}).then(r=>r.json()).then(d=>{
    showToast('檢查完成，重新載入中...');
    setTimeout(()=>location.reload(),1000);
  }).catch(()=>showToast('檢查失敗'));
}
"""
    html = render_page("總覽", "overview", content, js)
    resp = make_response(html)
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    return resp


# ==========================================
# 路由 - 客戶管理
# ==========================================

@app.route("/dashboard/clients")
def clients_list():
    if not is_authenticated():
        return redirect("/login")
    clients = get_all_clients()

    rows = ""
    for c in clients:
        health_ok = c.get("last_health_ok")
        checked = c.get("last_health_check")
        dot = "dot-green" if (checked and health_ok) else ("dot-red" if checked else "dot-grey")
        plan = PLAN_LABELS.get(c.get("billing", {}).get("plan", ""), "-")
        pay = PAYMENT_LABELS.get(c.get("billing", {}).get("payment_status", ""), "-")
        pay_class = "badge-green" if c.get("billing", {}).get("payment_status") == "paid" else ("badge-red" if c.get("billing", {}).get("payment_status") == "overdue" else "badge-orange")
        rows += f'''<tr onclick="location.href='/dashboard/clients/{c["id"]}'" style="cursor:pointer">
          <td><span class="dot {dot}"></span>{c["brand_name"]}</td>
          <td>{c.get("contact_person", "-")}</td>
          <td>{c.get("contact_phone", "-")}</td>
          <td>{plan}</td>
          <td><span class="badge {pay_class}">{pay}</span></td>
          <td>{c.get("deploy_date", "-")}</td>
        </tr>'''

    if not rows:
        rows = '<tr><td colspan="6" style="text-align:center;padding:30px;color:#ccc">還沒有客戶</td></tr>'

    content = f"""
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px">
      <div class="sec-title" style="margin:0">客戶列表</div>
      <a href="/dashboard/clients/new" class="btn btn-primary btn-sm">新增客戶</a>
    </div>
    <div class="card">
      <div class="table-wrap">
        <table>
          <tr><th>品牌名稱</th><th>聯絡人</th><th>電話</th><th>方案</th><th>付款狀態</th><th>部署日期</th></tr>
          {rows}
        </table>
      </div>
    </div>
    """
    html = render_page("客戶管理", "clients", content)
    resp = make_response(html)
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    return resp


@app.route("/dashboard/clients/new", methods=["GET", "POST"])
def client_new():
    if not is_authenticated():
        return redirect("/login")

    if request.method == "POST":
        client = {
            "id": str(uuid.uuid4()),
            "brand_name": request.form.get("brand_name", "").strip(),
            "industry": request.form.get("industry", "other"),
            "bot_url": request.form.get("bot_url", "").strip(),
            "admin_url": request.form.get("admin_url", "").strip(),
            "admin_password": request.form.get("admin_password", "").strip(),
            "railway_project_id": request.form.get("railway_project_id", "").strip(),
            "contact_person": request.form.get("contact_person", "").strip(),
            "contact_phone": request.form.get("contact_phone", "").strip(),
            "boss_user_id": request.form.get("boss_user_id", "").strip(),
            "line_token_hint": request.form.get("line_token_hint", "").strip(),
            "deploy_date": request.form.get("deploy_date", date.today().isoformat()),
            "notes": request.form.get("notes", "").strip(),
            "status": "active",
            "last_health_check": "",
            "last_health_ok": False,
            "billing": {
                "plan": request.form.get("plan", "standard"),
                "monthly_fee": int(request.form.get("monthly_fee", 0) or 0),
                "start_date": request.form.get("billing_start", date.today().isoformat()),
                "expiry_date": request.form.get("billing_expiry", ""),
                "payment_status": request.form.get("payment_status", "pending"),
                "payment_notes": ""
            },
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        save_client(client)
        return redirect(f"/dashboard/clients/{client['id']}")

    industry_options = "".join(f'<option value="{k}">{v}</option>' for k, v in INDUSTRY_LABELS.items())
    plan_options = "".join(f'<option value="{k}">{v}</option>' for k, v in PLAN_LABELS.items())
    payment_options = "".join(f'<option value="{k}">{v}</option>' for k, v in PAYMENT_LABELS.items())

    content = f"""
    <a href="/dashboard/clients" class="back-link">&larr; 返回客戶列表</a>
    <div class="card">
      <div class="card-title" style="margin-bottom:16px">新增客戶</div>
      <form method="POST">
        <div class="sec-title">基本資訊</div>
        <div class="form-row">
          <div class="form-group"><label>品牌名稱 *</label><input name="brand_name" required></div>
          <div class="form-group"><label>產業類別</label><select name="industry">{industry_options}</select></div>
        </div>
        <div class="form-row">
          <div class="form-group"><label>聯絡人</label><input name="contact_person"></div>
          <div class="form-group"><label>聯絡電話</label><input name="contact_phone"></div>
        </div>

        <div class="sec-title">部署資訊</div>
        <div class="form-row">
          <div class="form-group"><label>機器人網址</label><input name="bot_url" placeholder="https://xxx.up.railway.app"></div>
          <div class="form-group"><label>後台網址</label><input name="admin_url" placeholder="https://xxx.up.railway.app/admin"></div>
        </div>
        <div class="form-row">
          <div class="form-group"><label>後台密碼</label><input name="admin_password"></div>
          <div class="form-group"><label>Railway Project ID</label><input name="railway_project_id"></div>
        </div>
        <div class="form-row">
          <div class="form-group"><label>老闆 LINE User ID</label><input name="boss_user_id"></div>
          <div class="form-group"><label>LINE Token 提示（前8碼）</label><input name="line_token_hint" maxlength="8"></div>
        </div>
        <div class="form-group"><label>部署日期</label><input type="date" name="deploy_date" value="{date.today().isoformat()}"></div>

        <div class="sec-title">帳務資訊</div>
        <div class="form-row">
          <div class="form-group"><label>方案</label><select name="plan">{plan_options}</select></div>
          <div class="form-group"><label>月費 (TWD)</label><input type="number" name="monthly_fee" value="0"></div>
        </div>
        <div class="form-row">
          <div class="form-group"><label>計費開始</label><input type="date" name="billing_start" value="{date.today().isoformat()}"></div>
          <div class="form-group"><label>到期日</label><input type="date" name="billing_expiry"></div>
        </div>
        <div class="form-group"><label>付款狀態</label><select name="payment_status">{payment_options}</select></div>

        <div class="form-group"><label>備註</label><textarea name="notes" rows="3"></textarea></div>
        <button type="submit" class="btn btn-primary">儲存客戶</button>
      </form>
    </div>
    """
    html = render_page("新增客戶", "clients", content)
    resp = make_response(html)
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    return resp


@app.route("/dashboard/clients/<client_id>", methods=["GET", "POST"])
def client_detail(client_id):
    if not is_authenticated():
        return redirect("/login")
    client = get_client(client_id)
    if not client:
        return redirect("/dashboard/clients")

    if request.method == "POST":
        client["brand_name"] = request.form.get("brand_name", client["brand_name"]).strip()
        client["industry"] = request.form.get("industry", client.get("industry", "other"))
        client["bot_url"] = request.form.get("bot_url", "").strip()
        client["admin_url"] = request.form.get("admin_url", "").strip()
        client["admin_password"] = request.form.get("admin_password", "").strip()
        client["railway_project_id"] = request.form.get("railway_project_id", "").strip()
        client["contact_person"] = request.form.get("contact_person", "").strip()
        client["contact_phone"] = request.form.get("contact_phone", "").strip()
        client["boss_user_id"] = request.form.get("boss_user_id", "").strip()
        client["line_token_hint"] = request.form.get("line_token_hint", "").strip()
        client["deploy_date"] = request.form.get("deploy_date", client.get("deploy_date", ""))
        client["notes"] = request.form.get("notes", "").strip()
        client["billing"] = {
            "plan": request.form.get("plan", "standard"),
            "monthly_fee": int(request.form.get("monthly_fee", 0) or 0),
            "start_date": request.form.get("billing_start", ""),
            "expiry_date": request.form.get("billing_expiry", ""),
            "payment_status": request.form.get("payment_status", "pending"),
            "payment_notes": request.form.get("payment_notes", "")
        }
        save_client(client)
        return redirect(f"/dashboard/clients/{client_id}")

    c = client
    billing = c.get("billing", {})
    health_ok = c.get("last_health_ok")
    checked = c.get("last_health_check")
    if checked:
        dot = "dot-green" if health_ok else "dot-red"
        status_text = "運作中" if health_ok else "離線"
    else:
        dot = "dot-grey"
        status_text = "未檢查"

    industry_options = "".join(f'<option value="{k}" {"selected" if k==c.get("industry","") else ""}>{v}</option>' for k, v in INDUSTRY_LABELS.items())
    plan_options = "".join(f'<option value="{k}" {"selected" if k==billing.get("plan","") else ""}>{v}</option>' for k, v in PLAN_LABELS.items())
    payment_options = "".join(f'<option value="{k}" {"selected" if k==billing.get("payment_status","") else ""}>{v}</option>' for k, v in PAYMENT_LABELS.items())

    content = f"""
    <a href="/dashboard/clients" class="back-link">&larr; 返回客戶列表</a>

    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px">
      <div style="display:flex;align-items:center;gap:10px">
        <span class="dot {dot}"></span>
        <span style="font-size:18px;font-weight:600">{c["brand_name"]}</span>
        <span style="font-size:12px;color:#b0a090">{status_text}</span>
      </div>
      <div style="display:flex;gap:8px">
        <button class="btn btn-outline btn-sm" onclick="checkThis()">檢查健康</button>
        <a href="{c.get('admin_url', '#')}" target="_blank" class="btn btn-outline btn-sm">開啟後台</a>
        <button class="btn btn-danger btn-sm" onclick="deleteClient()">刪除客戶</button>
      </div>
    </div>

    <div class="card">
      <form method="POST">
        <div class="sec-title">基本資訊</div>
        <div class="form-row">
          <div class="form-group"><label>品牌名稱</label><input name="brand_name" value="{c.get('brand_name','')}"></div>
          <div class="form-group"><label>產業類別</label><select name="industry">{industry_options}</select></div>
        </div>
        <div class="form-row">
          <div class="form-group"><label>聯絡人</label><input name="contact_person" value="{c.get('contact_person','')}"></div>
          <div class="form-group"><label>聯絡電話</label><input name="contact_phone" value="{c.get('contact_phone','')}"></div>
        </div>

        <div class="sec-title">部署資訊</div>
        <div class="form-row">
          <div class="form-group"><label>機器人網址</label><input name="bot_url" value="{c.get('bot_url','')}"></div>
          <div class="form-group"><label>後台網址</label><input name="admin_url" value="{c.get('admin_url','')}"></div>
        </div>
        <div class="form-row">
          <div class="form-group"><label>後台密碼</label><input name="admin_password" value="{c.get('admin_password','')}"></div>
          <div class="form-group"><label>Railway Project ID</label><input name="railway_project_id" value="{c.get('railway_project_id','')}"></div>
        </div>
        <div class="form-row">
          <div class="form-group"><label>老闆 LINE User ID</label><input name="boss_user_id" value="{c.get('boss_user_id','')}"></div>
          <div class="form-group"><label>LINE Token 提示</label><input name="line_token_hint" value="{c.get('line_token_hint','')}" maxlength="8"></div>
        </div>
        <div class="form-group"><label>部署日期</label><input type="date" name="deploy_date" value="{c.get('deploy_date','')}"></div>

        <div class="sec-title">帳務資訊</div>
        <div class="form-row">
          <div class="form-group"><label>方案</label><select name="plan">{plan_options}</select></div>
          <div class="form-group"><label>月費 (TWD)</label><input type="number" name="monthly_fee" value="{billing.get('monthly_fee',0)}"></div>
        </div>
        <div class="form-row">
          <div class="form-group"><label>計費開始</label><input type="date" name="billing_start" value="{billing.get('start_date','')}"></div>
          <div class="form-group"><label>到期日</label><input type="date" name="billing_expiry" value="{billing.get('expiry_date','')}"></div>
        </div>
        <div class="form-row">
          <div class="form-group"><label>付款狀態</label><select name="payment_status">{payment_options}</select></div>
          <div class="form-group"><label>付款備註</label><input name="payment_notes" value="{billing.get('payment_notes','')}"></div>
        </div>

        <div class="form-group"><label>備註</label><textarea name="notes" rows="3">{c.get('notes','')}</textarea></div>
        <button type="submit" class="btn btn-primary">更新資料</button>
      </form>
    </div>
    """

    js = f"""
function checkThis(){{
  showToast('正在檢查...');
  fetch('/api/health-check',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{id:'{client_id}'}})}}
  ).then(r=>r.json()).then(()=>{{showToast('檢查完成');setTimeout(()=>location.reload(),1000)}}).catch(()=>showToast('檢查失敗'));
}}
function deleteClient(){{
  if(!confirm('確定要刪除 {c["brand_name"]} 嗎？此操作無法復原。'))return;
  fetch('/dashboard/clients/{client_id}/delete',{{method:'POST'}}).then(()=>location.href='/dashboard/clients');
}}
"""
    html = render_page(c["brand_name"], "clients", content, js)
    resp = make_response(html)
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    return resp


@app.route("/dashboard/clients/<client_id>/delete", methods=["POST"])
def client_delete(client_id):
    if not is_authenticated():
        return jsonify({"error": "unauthorized"}), 401
    delete_client(client_id)
    return jsonify({"status": "ok"})


# ==========================================
# 路由 - 帳務
# ==========================================

@app.route("/dashboard/billing")
def billing():
    if not is_authenticated():
        return redirect("/login")
    clients = get_all_clients()
    total_revenue = sum(c.get("billing", {}).get("monthly_fee", 0) for c in clients if c.get("billing", {}).get("payment_status") in ("paid", "pending"))
    paid_count = sum(1 for c in clients if c.get("billing", {}).get("payment_status") == "paid")

    rows = ""
    for c in clients:
        b = c.get("billing", {})
        plan = PLAN_LABELS.get(b.get("plan", ""), "-")
        fee = f"${b.get('monthly_fee', 0):,}"
        expiry = b.get("expiry_date", "-")
        status = b.get("payment_status", "")
        status_label = PAYMENT_LABELS.get(status, "-")
        badge_class = "badge-green" if status == "paid" else ("badge-red" if status == "overdue" else "badge-orange")
        rows += f'''<tr>
          <td><a href="/dashboard/clients/{c['id']}">{c["brand_name"]}</a></td>
          <td>{plan}</td>
          <td>{fee}</td>
          <td>{b.get("start_date", "-")}</td>
          <td>{expiry}</td>
          <td><span class="badge {badge_class}">{status_label}</span></td>
        </tr>'''

    if not rows:
        rows = '<tr><td colspan="6" style="text-align:center;padding:30px;color:#ccc">還沒有客戶</td></tr>'

    content = f"""
    <div class="stats" style="margin-bottom:14px">
      <div class="stat"><div class="stat-n">${total_revenue:,}</div><div class="stat-l">每月總收入</div></div>
      <div class="stat"><div class="stat-n green">{paid_count}</div><div class="stat-l">已付款</div></div>
      <div class="stat"><div class="stat-n orange">{len(clients) - paid_count}</div><div class="stat-l">待處理</div></div>
    </div>
    <div class="card">
      <div class="card-title" style="margin-bottom:12px">帳務總覽</div>
      <div class="table-wrap">
        <table>
          <tr><th>品牌名稱</th><th>方案</th><th>月費</th><th>計費開始</th><th>到期日</th><th>付款狀態</th></tr>
          {rows}
        </table>
      </div>
    </div>
    """
    html = render_page("帳務", "billing", content)
    resp = make_response(html)
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    return resp


# ==========================================
# 路由 - 模板庫
# ==========================================

@app.route("/dashboard/templates")
def templates_list():
    if not is_authenticated():
        return redirect("/login")
    templates = get_all_templates()

    cards = ""
    if templates:
        cards = '<div class="grid">'
        for t in templates:
            industry = INDUSTRY_LABELS.get(t.get("industry", ""), "其他")
            desc = t.get("description", "")[:60]
            cards += f'''
            <div class="client-card" onclick="location.href='/dashboard/templates/{t["id"]}'">
              <div class="client-card-top">
                <div class="client-card-name">{t["name"]}</div>
                <span class="badge badge-blue">{industry}</span>
              </div>
              <div class="client-card-info">{desc}</div>
              <div class="client-card-btns">
                <a href="/dashboard/templates/{t['id']}" class="btn btn-outline btn-sm" onclick="event.stopPropagation()">編輯</a>
              </div>
            </div>'''
        cards += '</div>'
    else:
        cards = '<div class="empty">還沒有模板</div>'

    content = f"""
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px">
      <div class="sec-title" style="margin:0">Prompt 模板庫</div>
      <a href="/dashboard/templates/new" class="btn btn-primary btn-sm">新增模板</a>
    </div>
    {cards}
    """
    html = render_page("模板庫", "templates", content)
    resp = make_response(html)
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    return resp


@app.route("/dashboard/templates/new", methods=["GET", "POST"])
def template_new():
    if not is_authenticated():
        return redirect("/login")

    if request.method == "POST":
        template = {
            "id": str(uuid.uuid4()),
            "name": request.form.get("name", "").strip(),
            "industry": request.form.get("industry", "other"),
            "description": request.form.get("description", "").strip(),
            "system_prompt": request.form.get("system_prompt", "").strip(),
            "trigger_words": [w.strip() for w in request.form.get("trigger_words", "").split("\n") if w.strip()],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        save_template(template)
        return redirect("/dashboard/templates")

    industry_options = "".join(f'<option value="{k}">{v}</option>' for k, v in INDUSTRY_LABELS.items())

    content = f"""
    <a href="/dashboard/templates" class="back-link">&larr; 返回模板庫</a>
    <div class="card">
      <div class="card-title" style="margin-bottom:16px">新增模板</div>
      <form method="POST">
        <div class="form-row">
          <div class="form-group"><label>模板名稱 *</label><input name="name" required></div>
          <div class="form-group"><label>產業類別</label><select name="industry">{industry_options}</select></div>
        </div>
        <div class="form-group"><label>說明</label><input name="description" placeholder="適用於..."></div>
        <div class="form-group"><label>System Prompt</label><textarea name="system_prompt" rows="14"></textarea></div>
        <div class="form-group"><label>轉人工關鍵字（一行一個）</label><textarea name="trigger_words" rows="5">找真人
找人工
找客服
找專員</textarea></div>
        <button type="submit" class="btn btn-primary">儲存模板</button>
      </form>
    </div>
    """
    html = render_page("新增模板", "templates", content)
    resp = make_response(html)
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    return resp


@app.route("/dashboard/templates/<template_id>", methods=["GET", "POST"])
def template_detail(template_id):
    if not is_authenticated():
        return redirect("/login")
    template = get_template(template_id)
    if not template:
        return redirect("/dashboard/templates")

    if request.method == "POST":
        template["name"] = request.form.get("name", "").strip()
        template["industry"] = request.form.get("industry", "other")
        template["description"] = request.form.get("description", "").strip()
        template["system_prompt"] = request.form.get("system_prompt", "").strip()
        template["trigger_words"] = [w.strip() for w in request.form.get("trigger_words", "").split("\n") if w.strip()]
        save_template(template)
        return redirect(f"/dashboard/templates/{template_id}")

    t = template
    industry_options = "".join(f'<option value="{k}" {"selected" if k==t.get("industry","") else ""}>{v}</option>' for k, v in INDUSTRY_LABELS.items())
    triggers_text = "\n".join(t.get("trigger_words", []))

    content = f"""
    <a href="/dashboard/templates" class="back-link">&larr; 返回模板庫</a>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px">
      <span style="font-size:18px;font-weight:600">{t["name"]}</span>
      <button class="btn btn-danger btn-sm" onclick="deleteTemplate()">刪除模板</button>
    </div>
    <div class="card">
      <form method="POST">
        <div class="form-row">
          <div class="form-group"><label>模板名稱</label><input name="name" value="{t.get('name','')}"></div>
          <div class="form-group"><label>產業類別</label><select name="industry">{industry_options}</select></div>
        </div>
        <div class="form-group"><label>說明</label><input name="description" value="{t.get('description','')}"></div>
        <div class="form-group"><label>System Prompt</label><textarea name="system_prompt" rows="14">{t.get('system_prompt','')}</textarea></div>
        <div class="form-group"><label>轉人工關鍵字（一行一個）</label><textarea name="trigger_words" rows="5">{triggers_text}</textarea></div>
        <button type="submit" class="btn btn-primary">更新模板</button>
      </form>
    </div>
    """

    js = f"""
function deleteTemplate(){{
  if(!confirm('確定要刪除這個模板嗎？'))return;
  fetch('/dashboard/templates/{template_id}/delete',{{method:'POST'}}).then(()=>location.href='/dashboard/templates');
}}
"""
    html = render_page(t["name"], "templates", content, js)
    resp = make_response(html)
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    return resp


@app.route("/dashboard/templates/<template_id>/delete", methods=["POST"])
def template_delete(template_id):
    if not is_authenticated():
        return jsonify({"error": "unauthorized"}), 401
    delete_template(template_id)
    return jsonify({"status": "ok"})


# ==========================================
# API 路由
# ==========================================

@app.route("/api/health-check", methods=["POST"])
def api_health_check():
    if not is_authenticated():
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    target_id = data.get("id")

    if target_id:
        client = get_client(target_id)
        if client and client.get("bot_url"):
            _, ok = check_single_health(client)
            db = _load_data()
            if target_id in db.get("clients", {}):
                db["clients"][target_id]["last_health_check"] = datetime.now().isoformat()
                db["clients"][target_id]["last_health_ok"] = ok
                _save_data(db)
            return jsonify({"id": target_id, "ok": ok})
        return jsonify({"error": "client not found"}), 404

    results = check_all_health()
    return jsonify({"results": {k: v for k, v in results.items()}})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
