# 部署与照片存储说明

## 照片是怎么存、怎么读的？

当前方案（轻量、无需对象存储）：

| 环节 | 位置 | 说明 |
|------|------|------|
| **文件本体** | `static/uploads/` | 上传后图片保存在此目录，文件名如 `20260501120000_二三.jpg` |
| **索引记录** | `site.db` → `photos` 表 | 存文件名、上传者、上传时间 |
| **网页读取** | Flask 静态路由 | 模板用 `url_for('static', filename='uploads/xxx.jpg')` 生成访问地址 |

流程：**上传 → 保存到 `static/uploads/` → 写入数据库 → 页面从数据库查列表 → 用静态 URL 展示图片**。

情书、账号数据在 `site.db`；时光轴在 `data/timeline.json`。

---

## 未上线前（本地阶段）建议怎么做

1. **本地跑通**  
   ```bash
   pip install -r requirements.txt
   python app.py
   ```  
   访问 http://127.0.0.1:5000 ，测试登录、上传、情书、时光轴。

2. **改好配置**（`app.py` 顶部）  
   - 账号密码 `USERS`  
   - 相恋日期 `LOVE_START_DATE` / `ANNIVERSARY_DATE`  
   - `SECRET_KEY` 改成随机长字符串  

3. **准备初始数据**  
   - 编辑 `data/timeline.json` 写好时光轴  
   - 本地可先上传一批照片，或把图片手动放进 `static/uploads/` 并在数据库插入记录（一般直接网页上传更简单）

4. **备份这两样**（上线前复制一份）  
   - `site.db`  
   - `static/uploads/` 整个文件夹  

5. **上线前关闭调试**  
   在 `app.py` 最后一行改为：  
   ```python
   app.run(host="0.0.0.0", port=5000, debug=False)
   ```  
   生产环境更推荐用 gunicorn（见下）。

---

## 服务器部署步骤（轻量云）

1. 把整个项目上传到服务器（含 `site.db`、`static/uploads/`、`data/timeline.json`）
2. 安装依赖：`pip install -r requirements.txt`
3. 确保目录可写：  
   ```bash
   chmod 755 static/uploads
   ```  
   （Windows 服务器保证 IIS/进程用户对 `uploads` 有写权限）
4. 启动（示例）：  
   ```bash
   pip install gunicorn
   gunicorn -w 2 -b 0.0.0.0:5000 app:app
   ```
5. 防火墙/安全组放行 **5000** 端口（或用 Nginx 反代到 80/443）

---

## 上线后如何备份照片？

定期备份：

- `static/uploads/`（所有图片文件）
- `site.db`（照片索引 + 情书 + 用户）
- `data/timeline.json`（时光轴）

三者一起拷走即可完整恢复。

---

## 以后照片很多怎么办？

当前方案适合情侣站点（几十～几百张）。若以后量很大，可考虑：

- 压缩上传图片（可在 `app.py` 里加 Pillow 缩略图）
- 对象存储（阿里云 OSS / 腾讯云 COS）+ 数据库只存 URL

现阶段 **不必提前做**，本地和轻量服务器完全够用。
