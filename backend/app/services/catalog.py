def get_store_catalog(store_id: int):
    return {
        "store": {
            "id": store_id,
            "merchant_id": 1,
            "name": "川香麻辣烫（中山店）",
            "business_status": "open",
            "business_hours": "10:00-22:30",
            "phone": "0760-12345678",
            "address": "中山市东区中山三路88号",
            "queue_prefix": "A",
            "avg_prepare_minutes": 18,
        },
        "dishes": [
            {"id": 1, "name": "招牌麻辣烫", "category": "推荐", "price": "12.00", "available": True},
            {"id": 2, "name": "牛肉串", "category": "荤菜", "price": "15.00", "available": True},
            {"id": 3, "name": "宽粉", "category": "主食", "price": "2.00", "available": True},
            {"id": 4, "name": "金针菇", "category": "素菜", "price": "3.00", "available": True},
            {"id": 5, "name": "冰粉", "category": "饮品", "price": "6.00", "available": True},
        ],
        "staff": [
            {"id": 1, "name": "张老板", "role": "boss", "status": "active"},
            {"id": 2, "name": "李店长", "role": "manager", "status": "active"},
            {"id": 3, "name": "王收银", "role": "cashier", "status": "active"},
            {"id": 4, "name": "赵师傅", "role": "cook", "status": "active"},
        ],
        "queue_rules": {
            "allow_customer_add_items": True,
            "allow_checkout_request": True,
            "max_active_sessions_per_customer": 1,
            "estimate_minutes_per_order": 5,
        },
    }


def get_platform_overview():
    return {
        "merchant_count": 128,
        "store_count": 186,
        "pending_merchants": 6,
        "pending_stores": 8,
        "today_sessions": 7682,
        "plans": [
            {"name": "免费版", "price": "0", "store_limit": 1, "features": ["基础叫号", "门店二维码"]},
            {"name": "基础版", "price": "298", "store_limit": 3, "features": ["多门店", "员工权限", "基础统计"]},
            {"name": "专业版", "price": "598", "store_limit": 10, "features": ["高级统计", "大屏叫号", "操作日志"]},
            {"name": "企业版", "price": "998", "store_limit": 0, "features": ["不限门店", "专属配置", "平台风控"]},
        ],
        "announcements": [
            {"title": "系统升级通知", "status": "published"},
            {"title": "新商家审核规则", "status": "draft"},
        ],
    }
