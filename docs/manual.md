# defect_manage 使用手册

面向两类人：**使用者**（产线检测人员、质检管理员）与**运维**（部署、备份、排障）。
架构与选型理由见 [`adr/`](adr/)；安装与开发流程见根目录 [`README.md`](../README.md)。

---

## 一、使用者

### 1.1 录入一条检测记录

1. 打开 <http://<服务器地址>:8000/defect/list/>，点「新增」。
2. 填写：

   | 字段 | 必填 | 说明 |
   |---|---|---|
   | 缺陷类型 | ✅ | 划痕 / 污渍 / 缺角 / 变形（可在后台维护） |
   | 检测人员 | ✅ | 录入人姓名或工号 |
   | 检测设备编号 | ✅ | 产出该图的设备，追溯用 |
   | 检测置信度 | ✅ | 0~1 之间（如 0.87） |
   | 原图 | ✅ | 检测原图 |
   | 缺陷标注图 | ⬜ | 带框的结果图，可暂缺 |
   | 备注 | ⬜ | 人工说明 |

3. 保存后自动跳回列表页。**检测时间由系统自动记录**，不需要手填。

### 1.2 查看与编辑

- **列表页**：按检测时间**由新到旧**排列，显示类型、人员、设备、置信度、时间。
- **详情页**：点某条记录的编号进入，可看到两张图片。
- **编辑**：详情页点「编辑」；改动会直接覆盖原记录。
- **删除**：点「删除」后会有一次确认页，确认后才真正删除（**不可恢复**）。

### 1.3 维护基础数据（管理员）

访问 <http://<服务器地址>:8000/admin/>，用管理员账号登录后可维护：

- **缺陷类型**：新增类型（如"气孔"）后，录入表单的下拉框立即出现该选项。
- **检测记录**：可按类型、人员筛选，也可批量删除——请谨慎。
- **用户**：为质检人员创建账号（本系统未开放自助注册）。

---

## 二、运维

### 2.1 启动

```powershell
# 注意：必须用装了 Django 的解释器(当前是 ODPlatform 的 venv)
& 'D:\ODPlatform\.venv\Scripts\python.exe' manage.py migrate      # 首次/升级后
& 'D:\ODPlatform\.venv\Scripts\python.exe' manage.py runserver 0.0.0.0:8000
```

生产部署前请先读 [`ADR-003`](adr/ADR-003-config-via-env.md)：**必须设置
`DJANGO_SECRET_KEY`、`DJANGO_DEBUG=false`、`DJANGO_ALLOWED_HOSTS`**。

### 2.2 备份与恢复

需要备份的只有两处：

| 内容 | 路径 | 说明 |
|---|---|---|
| 数据库 | `db.sqlite3` | 全部台账记录 |
| 图片 | `media/` | 原图与标注图 |

```powershell
# 备份(建议每天)
Copy-Item db.sqlite3 "backup\db-$(Get-Date -Format yyyyMMdd).sqlite3"
Compress-Archive media "backup\media-$(Get-Date -Format yyyyMMdd).zip" -Force

# 恢复
Copy-Item backup\db-20261024.sqlite3 db.sqlite3 -Force
Expand-Archive backup\media-20261024.zip . -Force
```

> 备份时建议先停服务（或至少确认没有正在上传的请求），避免拷到写了一半的数据库。

### 2.3 清库重建（确认数据可丢时）

```powershell
Remove-Item db.sqlite3
& 'D:\ODPlatform\.venv\Scripts\python.exe' manage.py migrate
& 'D:\ODPlatform\.venv\Scripts\python.exe' manage.py createsuperuser
```

### 2.4 排障对照表

| 现象 | 原因 | 处理 |
|---|---|---|
| `ModuleNotFoundError: No module named 'django'` | 用了系统 Python 而不是装了 Django 的解释器 | 用 `D:\ODPlatform\.venv\Scripts\python.exe`，或按 README 建独立 venv |
| 启动时出现 `RuntimeWarning: 未设置 DJANGO_SECRET_KEY` | 没配 `.env` | 复制 `.env.example` 为 `.env` 并填 `DJANGO_SECRET_KEY` |
| 重启后登录态失效 | 同上（每次重启换了随机密钥） | 同上 |
| 图片显示 404 | 开发模式未走 Django 托管 / `media/` 被移动 | 确认 `DEBUG=true` 且 `media/` 与 `db.sqlite3` 同级；生产需 Web 服务器托管 `/media/` |
| 上传报磁盘错误 | 磁盘满 | 清理或扩容；`media/` 与数据库所在盘要留余量 |
| 页面样式丢失 | `DEBUG=false` 时静态文件不由 Django 托管 | 用 `runserver`（开发）或由 Web 服务器托管 `/static/` |
| 新增记录报 `NOT NULL constraint failed` | 数据库结构与代码不一致（用过旧版迁移的库） | 备份后清库重建（见 2.3） |

### 2.5 日常检查清单

- [ ] `db.sqlite3` 与 `media/` 当天的备份是否生成
- [ ] 磁盘剩余空间（图片会持续增长）
- [ ] 应用日志中是否有 500 错误
- [ ] 列表页能正常打开、能上传一张测试图

---

## 三、数据字典

`DefectRecord`（检测记录）：

| 字段 | 类型 | 含义 |
|---|---|---|
| `defect_type` | 外键 → `DefectType` | 缺陷类型 |
| `detect_person` | 文本(50) | 检测人员 |
| `device_id` | 文本(50) | 检测设备编号 |
| `confidence` | 浮点 | 检测置信度（0~1） |
| `original_img` | 图片 | 原图，存 `media/original/` |
| `defect_img` | 图片 | 标注图，存 `media/defect_img/` |
| `detect_time` | 时间 | 录入时间，自动写入 |
| `remark` | 文本 | 备注 |

`DefectType`（缺陷类型）：`type_name`、`description`。

---

## 四、与检测链路的关系

本系统是**台账**，不负责检测：图片由检测环节（目标检测平台
[ODPlatform](https://github.com/chenkangkang999/ODPlatform)）产出后人工/程序上传到本系统。

> 当前代码处于初始版本，**尚未接回**自动推理与 LLM 研判接口。接回时请遵守两条约定：
> 1. 模型路径、数据指纹、运行 ID 等**不要写死在代码里**，走配置或环境变量；
> 2. 每条记录要能回溯到"哪一次推理、哪一版模型、哪一份数据指纹"（见 git 历史中
>    被撤销的那次迭代，或 `docs/adr/` 后续新增的 ADR）。