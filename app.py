# -*- coding: utf-8 -*-
"""
情侣互动网站 - 主程序
技术栈：Flask + SQLite + 会话登录
运行：python app.py  访问 http://127.0.0.1:5000
"""

import json
import os
import sqlite3
from datetime import datetime
from functools import wraps

from flask import (
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from flask_socketio import SocketIO, emit, disconnect, join_room, leave_room
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

app = Flask(__name__)
app.config["SECRET_KEY"] = "couple-secret-key-change-me-in-production"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 单张最大 8MB

# 初始化 SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")


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


@app.route("/photos")
@login_required
def photos():
    """照片墙（需登录查看与上传）"""
    db = get_db()
    photo_list = db.execute(
        "SELECT * FROM photos ORDER BY created_at DESC"
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
    return render_template("photos.html", user=current_user(), photos=valid_photos)


@app.route("/photos/upload", methods=["POST"])
@login_required
def upload_photo():
    """上传照片"""
    if "photo" not in request.files:
        flash("请选择一张图片", "warning")
        return redirect(url_for("photos"))

    file = request.files["photo"]
    if file.filename == "":
        flash("未选择文件", "warning")
        return redirect(url_for("photos"))

    if not allowed_file(file.filename):
        flash("仅支持 png、jpg、jpeg、gif、webp", "error")
        return redirect(url_for("photos"))

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
    return redirect(url_for("photos"))

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
    
    # 通过 SocketIO 实时通知
    diary_entry = {
        "id": db.execute("SELECT last_insert_rowid()").fetchone()[0],
        "content": content,
        "author": user["display_name"],
        "created_at": now,
    }
    socketio.emit(
        "new_diary",
        diary_entry,
        broadcast=True,
    )
    
    flash("心事发布成功～", "success")
    return redirect(url_for("secretdiary"))


@socketio.on("connect")
def handle_connect():
    """WebSocket 连接"""
    if session.get("user_id"):
        emit("response", {"data": "已连接"})


@socketio.on("disconnect")
def handle_disconnect():
    """WebSocket 断开连接"""
    pass


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
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, allow_unsafe_werkzeug=True)
