# LINE AI 客服管理中心

這是集中管理所有客戶 LINE AI 客服機器人的後台系統。

## 產品資訊
- 產品名稱：LINE AI 客服機器人
- 擁有者：chieh1580
- 用途：管理多個客戶的 LINE AI 聊天機器人

## 架構
- 單檔 Flask 應用（app.py），部署在 Railway
- 資料儲存：JSON 檔案掛載在 Railway Volume（/data/dashboard.json）
- 部署網址：https://dashboard-production-3e33.up.railway.app
- 登入密碼：Railway 環境變數 ADMIN_PASSWORD

## 功能
1. 總覽 — 所有客戶狀態一覽，健康檢查
2. 客戶管理 — 新增/編輯/刪除客戶資料
3. 帳務 — 方案、月費、付款狀態管理
4. 模板庫 — 預設 Prompt 模板（房地產、餐飲、美業）

## Railway 資訊
- Project ID: 41cdc48f-264d-4a38-84d7-ee6c0c2ef6af
- Service ID: 414e1b41-b822-41fa-a8ac-6e31d740ad71
- Environment ID: 38d19ca1-f7dc-434a-9b23-ed48396b397b
- API Token: Railway 帳號 chieh1580@gmail.com 的 token

## 部署方式
- 連結 GitHub repo（chieh1580/line-ai-dashboard）
- push 到 master 後需手動觸發部署（自動部署有時不穩定）
- Volume 掛載 /data，資料不會因重新部署而遺失

## 注意事項
- 所有回覆使用繁體中文
- 表單提交使用 JSON API（/api/clients），避免中文編碼問題
