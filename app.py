# -*- coding: utf-8 -*-
"""
情侣互动网站 - 主程序
技术栈：Flask + SQLite + 会话登录
运行：python app.py  访问 http://127.0.0.1:5000
"""

import json
import os
import random
import sqlite3
from datetime import datetime, timedelta
from functools import wraps

from flask import (
    Flask,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

# ========== 基础配置（可按需修改）==========
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("LOVE_DATA_DIR", "").strip()
if DATA_DIR:
    if not os.path.isabs(DATA_DIR):
        DATA_DIR = os.path.join(BASE_DIR, DATA_DIR)
    DATABASE = os.path.join(DATA_DIR, "site.db")
    UPLOAD_FOLDER = os.path.join(DATA_DIR, "uploads")
    TIMELINE_FILE = os.path.join(DATA_DIR, "timeline.json")
else:
    DATABASE = os.path.join(BASE_DIR, "site.db")
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    TIMELINE_FILE = os.path.join(BASE_DIR, "data", "timeline.json")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

# 相恋开始日期、纪念日（修改这里即可）
LOVE_START_DATE = "2026-05-28"
ANNIVERSARY_DATE = "2026-05-28"

# 两个固定账号（请改成你们的账号密码）
USERS = {
    "二三": {"password": "loveyy", "display_name": "二三"},
    "小六": {"password": "lovedfs", "display_name": "小六"},
}
CHECKIN_PLAYER_USERNAME = "小六"  # 单人模式：仅该账号可签到转盘
CHECKIN_JAR_TARGET_POINTS = 100
WISH_RECEIVER_USERNAME = "二三"
WISH_NOTE_MAX_LENGTH = 200
SPIN_REWARDS = [
    {
        "key": "cotton_hug",
        "name": "棉花糖拥抱",
        "short_name": "拥抱 +2",
        "icon": "🤍",
        "points": 2,
        "weight": 22,
    },
    {
        "key": "night_kiss",
        "name": "晚安亲亲",
        "short_name": "亲亲 +3",
        "icon": "💋",
        "points": 3,
        "weight": 19,
    },
    {
        "key": "cute_pass",
        "name": "撒娇特权券",
        "short_name": "特权 +4",
        "icon": "🧸",
        "points": 4,
        "weight": 16,
    },
    {
        "key": "movie_bonus",
        "name": "电影夜加成",
        "short_name": "电影 +5",
        "icon": "🎬",
        "points": 5,
        "weight": 14,
    },
    {
        "key": "milk_tea_day",
        "name": "奶茶投喂日",
        "short_name": "奶茶 +6",
        "icon": "🧋",
        "points": 6,
        "weight": 12,
    },
    {
        "key": "weekend_date",
        "name": "周末约会奖",
        "short_name": "约会 +8",
        "icon": "💞",
        "points": 8,
        "weight": 10,
    },
    {
        "key": "starlight_bonus",
        "name": "星光双倍礼",
        "short_name": "星光 +12",
        "icon": "✨",
        "points": 12,
        "weight": 6,
    },
    {
        "key": "ultimate_jackpot",
        "name": "终极大奖·心愿成真券",
        "short_name": "大奖 +30",
        "icon": "🌟",
        "points": 30,
        "weight": 1,
        "is_jackpot": True,
    },
]

app = Flask(__name__)
app.config["SECRET_KEY"] = "couple-secret-key-change-me-in-production"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 单张最大 8MB


# ========== 数据库 ==========
def get_db():
    """获取当前请求的数据库连接"""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    """请求结束关闭连接"""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """自动建表并初始化账号"""
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(os.path.dirname(TIMELINE_FILE), exist_ok=True)
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    cur = db.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            uploader TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS letters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            author TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS secretdiary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            author TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS checkin_spin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            display_name TEXT NOT NULL,
            reward_key TEXT NOT NULL,
            reward_name TEXT NOT NULL,
            reward_icon TEXT NOT NULL,
            points INTEGER NOT NULL,
            reward_index INTEGER NOT NULL,
            is_jackpot INTEGER NOT NULL DEFAULT 0,
            spin_date TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS points_jar (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            points INTEGER NOT NULL DEFAULT 0,
            target_points INTEGER NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS checkin_wish_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_username TEXT NOT NULL,
            sender_display_name TEXT NOT NULL,
            receiver_username TEXT NOT NULL,
            wish_note TEXT NOT NULL,
            jar_points INTEGER NOT NULL,
            jar_target_points INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_checkin_daily_user
        ON checkin_spin_logs(username, spin_date)
        """
    )
    cur.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_checkin_wish_receiver_created
        ON checkin_wish_notes(receiver_username, id DESC)
        """
    )
    # 初始化两个固定用户
    for username, info in USERS.items():
        row = cur.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        if row is None:
            cur.execute(
                "INSERT INTO users (username, password_hash, display_name) VALUES (?, ?, ?)",
                (
                    username,
                    generate_password_hash(info["password"]),
                    info["display_name"],
                ),
            )
    jar_row = cur.execute("SELECT id FROM points_jar WHERE id = 1").fetchone()
    if jar_row is None:
        cur.execute(
            "INSERT INTO points_jar (id, points, target_points, updated_at) VALUES (1, 0, ?, ?)",
            (CHECKIN_JAR_TARGET_POINTS, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )

    db.commit()
    db.close()


# ========== 工具函数 ==========
def allowed_file(filename):
    """检查是否为允许的图片格式"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def load_timeline():
    """从 data/timeline.json 读取时光轴，按日期倒序"""
    if not os.path.exists(TIMELINE_FILE):
        return []
    try:
        with open(TIMELINE_FILE, "r", encoding="utf-8") as f:
            events = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(events, list):
        return []
    return sorted(events, key=lambda x: x.get("event_date", ""), reverse=True)


def save_timeline(events):
    """保存时光轴到 data/timeline.json"""
    os.makedirs(os.path.dirname(TIMELINE_FILE), exist_ok=True)
    with open(TIMELINE_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)


def load_timeline_raw():
    """读取未排序的原始列表（用于增删改后写回）"""
    if not os.path.exists(TIMELINE_FILE):
        return []
    try:
        with open(TIMELINE_FILE, "r", encoding="utf-8") as f:
            events = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []
    return events if isinstance(events, list) else []

def get_checkin_player_display_name():
    """单人签到模式参与者展示名"""
    user_info = USERS.get(CHECKIN_PLAYER_USERNAME, {})
    return user_info.get("display_name", CHECKIN_PLAYER_USERNAME)


def is_checkin_player(user):
    """当前登录用户是否为单人签到模式参与者"""
    return bool(user) and user["username"] == CHECKIN_PLAYER_USERNAME

def get_wish_receiver_display_name():
    """心愿纸条接收者展示名"""
    receiver_info = USERS.get(WISH_RECEIVER_USERNAME, {})
    return receiver_info.get("display_name", WISH_RECEIVER_USERNAME)


def is_wish_receiver(user):
    """当前登录用户是否为心愿纸条接收账号"""
    return bool(user) and user["username"] == WISH_RECEIVER_USERNAME


def get_points_jar(db):
    """读取积分罐状态并计算进度"""
    row = db.execute(
        "SELECT points, target_points FROM points_jar WHERE id = 1"
    ).fetchone()
    if row is None:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.execute(
            "INSERT INTO points_jar (id, points, target_points, updated_at) VALUES (1, 0, ?, ?)",
            (CHECKIN_JAR_TARGET_POINTS, now_str),
        )
        db.commit()
        row = db.execute(
            "SELECT points, target_points FROM points_jar WHERE id = 1"
        ).fetchone()

    points = int(row["points"])
    target_points = int(row["target_points"]) if row["target_points"] else CHECKIN_JAR_TARGET_POINTS
    progress = 100.0 if target_points <= 0 else min(100.0, (points / target_points) * 100)
    return {
        "points": points,
        "target_points": target_points,
        "progress": round(progress, 1),
        "can_redeem": points >= target_points,
    }


def has_user_spun_today(db, username):
    """检查某个用户今天是否已经签到转盘"""
    today_str = datetime.now().strftime("%Y-%m-%d")
    row = db.execute(
        "SELECT id FROM checkin_spin_logs WHERE username = ? AND spin_date = ? LIMIT 1",
        (username, today_str),
    ).fetchone()
    return row is not None


def build_spin_rewards_for_view():
    """计算每个奖项的概率文案（用于展示）"""
    total_weight = sum(item["weight"] for item in SPIN_REWARDS) or 1
    reward_items = []
    for idx, reward in enumerate(SPIN_REWARDS):
        reward_items.append(
            {
                "index": idx,
                "key": reward["key"],
                "name": reward["name"],
                "short_name": reward["short_name"],
                "icon": reward["icon"],
                "points": reward["points"],
                "weight": reward["weight"],
                "probability": round((reward["weight"] / total_weight) * 100, 1),
                "is_jackpot": bool(reward.get("is_jackpot", False)),
            }
        )
    return reward_items


def draw_spin_reward():
    """按权重抽取转盘奖励"""
    reward_indexes = list(range(len(SPIN_REWARDS)))
    reward_weights = [item["weight"] for item in SPIN_REWARDS]
    reward_index = random.choices(reward_indexes, weights=reward_weights, k=1)[0]
    return reward_index, SPIN_REWARDS[reward_index]


def get_today_spin_log(db, username):
    """读取某个用户今天的签到记录"""
    today_str = datetime.now().strftime("%Y-%m-%d")
    return db.execute(
        """
        SELECT
            reward_key, reward_name, reward_icon, points,
            reward_index, is_jackpot, spin_date, created_at
        FROM checkin_spin_logs
        WHERE username = ? AND spin_date = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (username, today_str),
    ).fetchone()


def normalize_checkin_history_period(period):
    """规范化签到历史筛选周期，仅支持 week/month"""
    period_value = (period or "").strip().lower()
    return "week" if period_value == "week" else "month"


def get_checkin_history_start_date(period):
    """根据周期返回签到历史查询起始日期"""
    today = datetime.now().date()
    if period == "week":
        return today - timedelta(days=today.weekday())
    return today.replace(day=1)


def get_checkin_history_logs(db, username, period):
    """读取签到历史列表（按本周/本月筛选）"""
    normalized_period = normalize_checkin_history_period(period)
    start_date = get_checkin_history_start_date(normalized_period).strftime("%Y-%m-%d")
    rows = db.execute(
        """
        SELECT reward_name, reward_icon, points, is_jackpot, created_at
        FROM checkin_spin_logs
        WHERE username = ? AND spin_date >= ?
        ORDER BY id DESC
        """,
        (username, start_date),
    ).fetchall()
    logs = [
        {
            "reward_name": row["reward_name"],
            "reward_icon": row["reward_icon"],
            "points": int(row["points"]),
            "is_jackpot": bool(row["is_jackpot"]),
            "created_at": row["created_at"],
        }
        for row in rows
    ]
    return normalized_period, logs


def login_required(view):
    """登录装饰器"""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("请先登录～", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def current_user():
    """当前登录用户信息"""
    if not session.get("user_id"):
        return None
    db = get_db()
    return db.execute(
        "SELECT id, username, display_name FROM users WHERE id = ?",
        (session["user_id"],),
    ).fetchone()


# ========== 路由 ==========
@app.route("/login", methods=["GET", "POST"])
def login():
    """登录页"""
    if session.get("user_id"):
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["display_name"] = user["display_name"]
            flash(f"欢迎回来，{user['display_name']}～", "success")
            return redirect(url_for("index"))
        flash("账号或密码错误", "error")

    return render_template("login.html", users=list(USERS.keys()))


@app.route("/logout")
def logout():
    """退出登录"""
    session.clear()
    flash("已退出登录，下次见～", "info")
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    """主页：相恋计时、纪念日倒计时、时光轴（需登录）"""
    events = load_timeline()
    user = current_user()
    return render_template(
        "index.html",
        user=user,
        love_start=LOVE_START_DATE,
        anniversary=ANNIVERSARY_DATE,
        events=events,
    )


@app.route("/checkin")
@login_required
def checkin():
    """签到转盘页（单人模式）"""
    db = get_db()
    user = current_user()
    checkin_player_name = get_checkin_player_display_name()
    points_jar = get_points_jar(db)
    spin_rewards = build_spin_rewards_for_view()
    player_spun_today = has_user_spun_today(db, CHECKIN_PLAYER_USERNAME)
    today_spin_log = get_today_spin_log(db, CHECKIN_PLAYER_USERNAME)
    is_checkin_player_user = is_checkin_player(user)
    can_spin = is_checkin_player_user and (not player_spun_today)
    history_period, recent_logs = get_checkin_history_logs(
        db, CHECKIN_PLAYER_USERNAME, "month"
    )
    return render_template(
        "checkin.html",
        user=user,
        checkin_player_name=checkin_player_name,
        wish_receiver_name=get_wish_receiver_display_name(),
        wish_note_max_length=WISH_NOTE_MAX_LENGTH,
        is_checkin_player_user=is_checkin_player_user,
        can_spin=can_spin,
        player_spun_today=player_spun_today,
        today_spin_log=today_spin_log,
        points_jar=points_jar,
        spin_rewards=spin_rewards,
        recent_logs=recent_logs,
        history_period=history_period,
    )


@app.route("/checkin/history")
@login_required
def checkin_history():
    """签到历史查询（支持本周/本月筛选）"""
    db = get_db()
    period, logs = get_checkin_history_logs(
        db, CHECKIN_PLAYER_USERNAME, request.args.get("period", "month")
    )
    return jsonify(
        {
            "ok": True,
            "period": period,
            "period_text": "本周" if period == "week" else "本月",
            "logs": logs,
        }
    )

@app.route("/checkin/wishes")
@login_required
def checkin_wishes():
    """心愿纸条查询（仅接收账号可查看）"""
    user = current_user()
    if not is_wish_receiver(user):
        return (
            jsonify(
                {
                    "ok": False,
                    "message": f"仅 {get_wish_receiver_display_name()} 可查看心愿纸条",
                }
            ),
            403,
        )

    db = get_db()
    rows = db.execute(
        """
        SELECT
            id, sender_username, sender_display_name, wish_note,
            jar_points, jar_target_points, created_at
        FROM checkin_wish_notes
        WHERE receiver_username = ?
        ORDER BY id DESC
        """,
        (user["username"],),
    ).fetchall()
    wishes = [
        {
            "id": row["id"],
            "sender_username": row["sender_username"],
            "sender_display_name": row["sender_display_name"],
            "wish_note": row["wish_note"],
            "jar_points": int(row["jar_points"]),
            "jar_target_points": int(row["jar_target_points"]),
            "created_at": row["created_at"],
        }
        for row in rows
    ]
    return jsonify(
        {
            "ok": True,
            "receiver_username": user["username"],
            "receiver_display_name": user["display_name"],
            "wishes": wishes,
        }
    )


@app.route("/checkin/spin", methods=["POST"])
@login_required
def checkin_spin():
    """执行一次签到转盘"""
    user = current_user()
    if not is_checkin_player(user):
        return (
            jsonify(
                {
                    "ok": False,
                    "message": f"当前为单人模式，仅 {get_checkin_player_display_name()} 可以签到",
                }
            ),
            403,
        )

    db = get_db()
    if has_user_spun_today(db, user["username"]):
        return jsonify({"ok": False, "message": "今天已经签到过啦，明天再来～"}), 400

    reward_index, reward = draw_spin_reward()
    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    today_str = now.strftime("%Y-%m-%d")
    total_weight = sum(item["weight"] for item in SPIN_REWARDS) or 1

    try:
        get_points_jar(db)
        db.execute(
            """
            INSERT INTO checkin_spin_logs (
                username, display_name, reward_key, reward_name, reward_icon,
                points, reward_index, is_jackpot, spin_date, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user["username"],
                user["display_name"],
                reward["key"],
                reward["name"],
                reward["icon"],
                reward["points"],
                reward_index,
                1 if reward.get("is_jackpot", False) else 0,
                today_str,
                now_str,
            ),
        )
        db.execute(
            "UPDATE points_jar SET points = points + ?, updated_at = ? WHERE id = 1",
            (reward["points"], now_str),
        )
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback()
        return jsonify({"ok": False, "message": "今天已经签到过啦，明天再来～"}), 400

    jar_state = get_points_jar(db)
    return jsonify(
        {
            "ok": True,
            "message": "签到成功～",
            "reward": {
                "index": reward_index,
                "key": reward["key"],
                "name": reward["name"],
                "short_name": reward["short_name"],
                "icon": reward["icon"],
                "points": reward["points"],
                "probability": round((reward["weight"] / total_weight) * 100, 1),
                "is_jackpot": bool(reward.get("is_jackpot", False)),
            },
            "points_jar": jar_state,
        }
    )


@app.route("/checkin/redeem", methods=["POST"])
@login_required
def checkin_redeem():
    """积分罐达标后提交心愿纸条并重置积分"""
    user = current_user()
    if not is_checkin_player(user):
        return (
            jsonify(
                {
                    "ok": False,
                    "message": f"当前为单人模式，仅 {get_checkin_player_display_name()} 可以领取",
                }
            ),
            403,
        )

    db = get_db()
    jar_state = get_points_jar(db)
    if not jar_state["can_redeem"]:
        return jsonify({"ok": False, "message": "积分还没攒满，继续努力呀～"}), 400
    request_json = request.get_json(silent=True)
    if isinstance(request_json, dict):
        wish_note = str(request_json.get("wish_note", "")).strip()
    else:
        wish_note = ""
    if not wish_note:
        wish_note = request.form.get("wish_note", "").strip()
    if not wish_note:
        return jsonify({"ok": False, "message": "请先写下心愿纸条再提交哦～"}), 400
    if len(wish_note) > WISH_NOTE_MAX_LENGTH:
        return (
            jsonify(
                {
                    "ok": False,
                    "message": f"心愿纸条最多 {WISH_NOTE_MAX_LENGTH} 字，请精简后再提交～",
                }
            ),
            400,
        )

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    receiver_name = get_wish_receiver_display_name()
    db.execute(
        """
        INSERT INTO checkin_wish_notes (
            sender_username, sender_display_name, receiver_username,
            wish_note, jar_points, jar_target_points, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user["username"],
            user["display_name"],
            WISH_RECEIVER_USERNAME,
            wish_note,
            jar_state["points"],
            jar_state["target_points"],
            now_str,
        ),
    )
    db.execute(
        "UPDATE points_jar SET points = 0, updated_at = ? WHERE id = 1",
        (now_str,),
    )
    db.commit()
    new_state = get_points_jar(db)
    return jsonify(
        {
            "ok": True,
            "message": f"心愿纸条已送达 {receiver_name}，积分罐已清零，开启下一轮甜蜜积攒吧～",
            "points_jar": new_state,
        }
    )


@app.route("/photos")
@login_required
def photos():
    """照片墙（需登录查看与上传）"""
    heart_page_size = 24
    db = get_db()
    photo_list = db.execute(
        "SELECT * FROM photos ORDER BY created_at ASC, id ASC"
    ).fetchall()
    # 过滤出真实存在的照片，删除找不到的记录
    valid_photos = []
    invalid_photo_ids = []
    for photo in photo_list:
        photo_path = os.path.join(UPLOAD_FOLDER, photo["filename"])
        if os.path.exists(photo_path):
            valid_photos.append(photo)
        else:
            invalid_photo_ids.append(photo["id"])
    # 删除不存在的照片数据库记录
    if invalid_photo_ids:
        placeholders = ",".join("?" * len(invalid_photo_ids))
        db.execute(f"DELETE FROM photos WHERE id IN ({placeholders})", invalid_photo_ids)
        db.commit()
    total_photos = len(valid_photos)
    max_page = max(1, (total_photos // heart_page_size) + 1)
    page_str = request.args.get("page", "1").strip()
    page = int(page_str) if page_str.isdigit() else 1
    page = max(1, min(page, max_page))
    start = (page - 1) * heart_page_size
    end = start + heart_page_size
    page_photos = valid_photos[start:end]
    return render_template(
        "photos.html",
        user=current_user(),
        photos=page_photos,
        page=page,
        max_page=max_page,
        heart_page_size=heart_page_size,
        total_photos=total_photos,
    )


@app.route("/photos/upload", methods=["POST"])
@login_required
def upload_photo():
    """上传照片"""
    page_str = request.form.get("page", "1").strip()
    page = int(page_str) if page_str.isdigit() else 1
    page = max(1, page)
    if "photo" not in request.files:
        flash("请选择一张图片", "warning")
        return redirect(url_for("photos", page=page))

    file = request.files["photo"]
    if file.filename == "":
        flash("未选择文件", "warning")
        return redirect(url_for("photos", page=page))

    if not allowed_file(file.filename):
        flash("仅支持 png、jpg、jpeg、gif、webp", "error")
        return redirect(url_for("photos", page=page))

    original = secure_filename(file.filename)
    ext = original.rsplit(".", 1)[1].lower()
    new_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{session['username']}.{ext}"
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], new_name)
    file.save(save_path)

    db = get_db()
    db.execute(
        "INSERT INTO photos (filename, uploader, created_at) VALUES (?, ?, ?)",
        (new_name, session["display_name"], datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    db.commit()
    flash("照片上传成功～", "success")
    return redirect(url_for("photos", page=page))

@app.route("/photos/delete/<int:photo_id>", methods=["POST"])
@login_required
def delete_photo(photo_id):
    """删除照片（删除记录并尝试删除文件）"""
    db = get_db()
    photo = db.execute("SELECT id, filename FROM photos WHERE id = ?", (photo_id,)).fetchone()
    if photo is None:
        flash("照片不存在或已删除", "warning")
        return redirect(url_for("photos"))

    upload_root = os.path.abspath(app.config["UPLOAD_FOLDER"])
    file_path = os.path.abspath(os.path.join(upload_root, photo["filename"]))
    if os.path.commonpath([upload_root, file_path]) == upload_root and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError:
            flash("照片记录已删除，文件清理失败", "warning")

    db.execute("DELETE FROM photos WHERE id = ?", (photo_id,))
    db.commit()
    flash("照片已删除", "success")
    return redirect(url_for("photos"))

@app.route("/photos/delete-batch", methods=["POST"])
@login_required
def delete_photos_batch():
    """批量删除照片（删除记录并尝试删除文件）"""
    raw_ids = request.form.get("photo_ids", "")
    photo_ids = []
    for item in raw_ids.split(","):
        item = item.strip()
        if not item:
            continue
        if item.isdigit():
            photo_ids.append(int(item))
    photo_ids = list(dict.fromkeys(photo_ids))
    if not photo_ids:
        flash("请先选择要删除的照片", "warning")
        return redirect(url_for("photos"))

    db = get_db()
    placeholders = ",".join("?" * len(photo_ids))
    photos = db.execute(
        f"SELECT id, filename FROM photos WHERE id IN ({placeholders})", photo_ids
    ).fetchall()
    if not photos:
        flash("未找到可删除的照片", "warning")
        return redirect(url_for("photos"))

    upload_root = os.path.abspath(app.config["UPLOAD_FOLDER"])
    for photo in photos:
        file_path = os.path.abspath(os.path.join(upload_root, photo["filename"]))
        if os.path.commonpath([upload_root, file_path]) == upload_root and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass

    existing_ids = [photo["id"] for photo in photos]
    delete_placeholders = ",".join("?" * len(existing_ids))
    db.execute(f"DELETE FROM photos WHERE id IN ({delete_placeholders})", existing_ids)
    db.commit()
    flash(f"已删除 {len(existing_ids)} 张照片", "success")
    return redirect(url_for("photos"))


@app.route("/uploads/<path:filename>")
@login_required
def uploaded_file(filename):
    """访问上传目录中的照片（支持独立数据目录）"""
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/letters")
@login_required
def letters():
    """情书墙（需登录查看与发布）"""
    db = get_db()
    letter_list = db.execute(
        "SELECT * FROM letters ORDER BY created_at DESC"
    ).fetchall()
    return render_template("letters.html", user=current_user(), letters=letter_list)


@app.route("/letters/publish", methods=["POST"])
@login_required
def publish_letter():
    """发布情书"""
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    if not title or not content:
        flash("标题和内容都不能为空哦", "warning")
        return redirect(url_for("letters"))

    db = get_db()
    db.execute(
        "INSERT INTO letters (title, content, author, created_at) VALUES (?, ?, ?, ?)",
        (
            title,
            content,
            session["display_name"],
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )
    db.commit()
    flash("情书发布成功～", "success")
    return redirect(url_for("letters"))


@app.route("/secretdiary")
@login_required
def secretdiary():
    """心事墙（需登录）"""
    db = get_db()
    diary_list = db.execute(
        "SELECT * FROM secretdiary ORDER BY created_at DESC"
    ).fetchall()
    return render_template("secretdiary.html", user=current_user(), diaries=diary_list)


@app.route("/secretdiary/post", methods=["POST"])
@login_required
def post_secretdiary():
    """发布心事"""
    content = request.form.get("content", "").strip()
    if not content:
        flash("心事内容不能为空哦", "warning")
        return redirect(url_for("secretdiary"))

    db = get_db()
    user = current_user()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    db.execute(
        "INSERT INTO secretdiary (content, author, created_at) VALUES (?, ?, ?)",
        (content, user["display_name"], now),
    )
    db.commit()
    flash("心事发布成功～", "success")
    return redirect(url_for("secretdiary"))


@app.route("/timeline/add", methods=["POST"])
@login_required
def add_timeline():
    """添加一条时光轴事件"""
    event_date = request.form.get("event_date", "").strip()
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()

    if not event_date or not title or not content:
        flash("日期、标题和内容不能为空", "warning")
        return redirect(url_for("index"))

    events = load_timeline_raw()
    # 找最大 ID
    max_id = max((e.get("id", 0) for e in events), default=0)
    new_event = {
        "id": max_id + 1,
        "event_date": event_date,
        "title": title,
        "content": content,
    }
    events.append(new_event)
    save_timeline(events)
    flash("时光轴事件添加成功～", "success")
    return redirect(url_for("index"))


@app.route("/timeline/edit/<int:event_id>", methods=["POST"])
@login_required
def edit_timeline(event_id):
    """编辑一条时光轴事件"""
    event_date = request.form.get("event_date", "").strip()
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()

    if not event_date or not title or not content:
        flash("日期、标题和内容不能为空", "warning")
        return redirect(url_for("index"))

    events = load_timeline_raw()
    event_found = False
    for event in events:
        if event.get("id") == event_id:
            event["event_date"] = event_date
            event["title"] = title
            event["content"] = content
            event_found = True
            break

    if not event_found:
        flash("未找到该事件", "warning")
    else:
        save_timeline(events)
        flash("时光轴事件编辑成功～", "success")
    return redirect(url_for("index"))


@app.route("/timeline/delete/<int:event_id>", methods=["POST"])
@login_required
def delete_timeline(event_id):
    """删除一条时光轴事件（写回 JSON 文件）"""
    events = load_timeline_raw()
    new_events = [e for e in events if e.get("id") != event_id]
    if len(new_events) == len(events):
        flash("未找到该事件", "warning")
    else:
        save_timeline(new_events)
        flash("已删除该时光轴事件", "success")
    return redirect(url_for("index"))


# ========== 启动 ==========
if __name__ == "__main__":
    init_db()
    # host=0.0.0.0 便于轻量服务器外网访问；仅本机可改为 127.0.0.1
    app.run(host="0.0.0.0", port=5000, debug=True)
