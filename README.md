# 我们的小窝 · 情侣互动网站

轻量级情侣互动站点：Flask + SQLite + 本地 CSS（Tailwind 风格类名）+ 原生 JS，纯本地运行，无 CDN 依赖。

## 功能

- 双账号登录（仅「我」和「女朋友」）
- 恋爱时光轴（从 `data/timeline.json` 读取，登录后可删除）
- 照片墙（登录后上传，永久保存）
- 情书墙（登录后发布，带时间）
- 会话保持，数据存 SQLite，重启不丢失

## 快速开始

```bash
# 1. 进入项目目录
cd 二三得六

# 2. 安装依赖（仅需 Flask）
pip install -r requirements.txt

# 3. 运行（首次自动创建 site.db 和 uploads 目录）
python app.py
```

浏览器打开：http://127.0.0.1:5000

默认账号（在 `app.py` 的 `USERS` 中修改）：

| 账号     | 默认密码   |
|----------|------------|
| 我       | love2024   |
| 女朋友   | love2024   |

## 自定义配置

编辑 `app.py` 顶部：

- `LOVE_START_DATE`：相恋开始日期
- `ANNIVERSARY_DATE`：纪念日
- `USERS`：两个账号与密码
- `DEFAULT_TIMELINE`：时光轴初始事件
- `SECRET_KEY`：生产环境请改成随机字符串

## 时光轴配置

编辑 `data/timeline.json`，每条事件格式如下（`id` 需唯一）：

```json
{
  "id": 1,
  "event_date": "2026-05-28",
  "title": "我们在一起了",
  "content": "那一天，世界变得特别温柔。"
}
```

登录后在首页可点击「删除」移除单条；也可直接改 JSON 文件后刷新页面。旧版数据库里的 timeline 表已不再使用。

## 目录结构

```
二三得六/
├── app.py              # 主程序
├── data/
│   └── timeline.json   # 时光轴数据（部署时直接编辑此文件）
├── site.db             # 运行后自动生成的数据库
├── requirements.txt
├── templates/          # HTML 页面
├── static/
│   ├── css/style.css
│   ├── js/main.js
│   └── uploads/        # 上传的图片
└── README.md
```

## 部署轻量服务器

```bash
pip install -r requirements.txt
# 生产环境建议关闭 debug，并用 gunicorn 等（可选）
python app.py
```

监听 `0.0.0.0:5000`，记得在安全组放行端口，并修改默认密码与 `SECRET_KEY`。
