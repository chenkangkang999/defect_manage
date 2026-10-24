# defect_manage

缺陷检测台账管理系统 —— 记录、查看与管理工业缺陷检测结果的 Django Web 应用。

> ⚠️ **当前状态**：仓库处于**初始版本**。原 W1/W2/W3 迭代（数据血缘字段、DRF 接口、
> 统计看板/复核队列/热力图、YOLO 推理接口、DeepSeek LLM 研判）已通过一次 revert 提交
> 撤销，代码不在当前工作树中（仍在 git 历史里，如需找回对那次 revert 再 revert 一次即可）。

## 功能

| 页面 | 路径 | 说明 |
|---|---|---|
| 缺陷列表 | `/defect/list/` | 按检测时间倒序展示全部记录 |
| 新增记录 | `/defect/add/` | 上传原图/标注图并填写检测信息 |
| 记录详情 | `/defect/detail/<id>/` | 单条记录完整信息 |
| 编辑记录 | `/defect/edit/<id>/` | 修改已有记录 |
| 删除记录 | `/defect/delete/<id>/` | 二次确认后删除 |
| 管理后台 | `/admin/` | Django Admin（缺陷类型、记录、用户） |

数据模型只有两张表：`DefectType`（缺陷类型：划痕/污渍/缺角/变形）与 `DefectRecord`
（检测记录：类型、检测人员、设备编号、置信度、原图、标注图、检测时间、备注）。

## 环境要求

- **Python 3.12**（与 `requirements.txt` 中 Django 6.1.2 匹配）
- 依赖见 [`requirements.txt`](requirements.txt)：Django、djangorestframework、
  django-cors-headers、pillow

> **⭐ 重要：用哪个解释器**
> 本项目**没有自己的虚拟环境**，当前依赖装在 ODPlatform 的 venv 里
> （`D:\ODPlatform\.venv`，`Django 6.1.2` 只装在那里）。所以：
>
> ```powershell
> # ✅ 能跑起来
> & 'D:\ODPlatform\.venv\Scripts\python.exe' manage.py runserver
> # ❌ 会报 ModuleNotFoundError: No module named 'django'
> python manage.py runserver
> ```
>
> 这是历史遗留的耦合（两个项目共用一套依赖，互相升级都可能碰坏对方）。
> **建议为本项目单独建 venv**：见下文「独立虚拟环境（推荐）」。

## 安装

```powershell
# 方式 A：沿用现有环境（最快，但有耦合风险）
& 'D:\ODPlatform\.venv\Scripts\python.exe' -m pip install -r requirements.txt

# 方式 B（推荐）：独立虚拟环境，与 ODPlatform 解耦
python -m venv .venv
& '.\.venv\Scripts\python.exe' -m pip install --upgrade pip
& '.\.venv\Scripts\python.exe' -m pip install -r requirements.txt
```

> 若后续要接回 YOLO 推理，需要额外安装 `ultralytics` 与 `opencv-python`；
> 要用 GPU 还必须装 **CUDA 版 torch**（PyPI 默认可能给 `+cpu` 构建，会让 GPU 静默失效）：
>
> ```powershell
> pip install torch torchvision --index-url https://download.pytorch.org/whl/cu126
> ```
>
> 版本要与本机显卡驱动匹配（例如驱动 561.19 对应 CUDA 12.6 上限）。

## 配置（环境变量）

配置全部走环境变量，可以写在项目根的 `.env`（模板见 [`.env.example`](.env.example)，
`.env` 已被 `.gitignore` 忽略，不会进 git）。`settings.py` 启动时自动读取它，
**真实的系统环境变量优先级更高**。

| 变量 | 默认值 | 说明 |
|---|---|---|
| `DJANGO_SECRET_KEY` | 无（开发环境用一次性随机值并告警） | 生产必填；生成：`python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `DJANGO_DEBUG` | `true` | 生产必须设 `false` |
| `DJANGO_ALLOWED_HOSTS` | 空 | 逗号分隔；`DEBUG=true` 时可留空 |
| `DJANGO_CORS_ALLOW_ALL` | `true` | 生产改成 `false` 并配白名单 |
| `DJANGO_LANGUAGE_CODE` | `en-us` | 中文界面填 `zh-hans` |
| `DJANGO_TIME_ZONE` | `UTC` | 例如 `Asia/Shanghai` |

没有 `DJANGO_SECRET_KEY` 时开发环境不会崩，但**每次重启都会换密钥**（登录态与签名失效），
并打印一条 `RuntimeWarning` 提醒。

## 运行

```powershell
# 1) 建库（首次或模型变更后）
& 'D:\ODPlatform\.venv\Scripts\python.exe' manage.py migrate

# 2) 启动开发服务器
& 'D:\ODPlatform\.venv\Scripts\python.exe' manage.py runserver 8000

# 3) 可选：创建后台管理员
& 'D:\ODPlatform\.venv\Scripts\python.exe' manage.py createsuperuser
```

打开 <http://127.0.0.1:8000/defect/list/>。上传的图片写入 `media/`
（`media/original/`、`media/defect_img/`），通过 `/media/` 暴露（仅开发模式）。

## 数据库

- SQLite，文件 `db.sqlite3`，位于项目根，**未被 git 跟踪**（属于本地数据）。
- 备份：直接复制 `db.sqlite3` 即可；媒体文件另需备份 `media/`。
- 重建（数据可丢时）：删除 `db.sqlite3` 后重新 `manage.py migrate`。
- 迁移检查（CI 也跑这条）：`manage.py makemigrations --check --dry-run`，输出
  `No changes detected` 才算模型与迁移一致。

## 开发流程

1. 从 `main` 拉分支：`git checkout -b feat/<简短描述>`。
2. 改动后本地自检（与 CI 等价）：
   ```powershell
   & 'D:\ODPlatform\.venv\Scripts\python.exe' manage.py check
   & 'D:\ODPlatform\.venv\Scripts\python.exe' manage.py makemigrations --check --dry-run
   & 'D:\ODPlatform\.venv\Scripts\python.exe' manage.py test -v 2
   ```
3. 提交信息用中文约定式前缀：`feat:` / `fix:` / `refactor:` / `chore:` / `docs:`。
4. 推分支并开 PR，等 CI 绿灯后合并。

### 编码约定（重要）

- **不硬编码**：路径用 `settings.BASE_DIR` 推导；密钥/主机名/开关一律走环境变量；
  端口、外部地址、模型路径等可变量不要写死在代码里。
- **不留魔法数字**：有业务含义的阈值要有名字（放常量或配置），并写清单位与含义。
- **改配置就要改文档**：新增环境变量同步更新 `.env.example` 与本 README 的表格。

## 测试

`defect/tests.py` 目前是 Django 的空占位（还没有测试），`manage.py test` 会通过但不覆盖
任何逻辑。**新增功能请配套写测试**；测试放 `defect/tests.py` 或 `defect/tests/` 包下。

## CI

工作流：[`.github/workflows/ci.yml`](.github/workflows/ci.yml)，在 push 到 `main` 与
PR 时触发，跑四件事：

1. `manage.py check` —— Django 系统检查
2. `manage.py makemigrations --check --dry-run` —— 迁移是否有遗漏
3. `manage.py test` —— 测试
4. **硬编码守卫** —— 扫描 `.py/.html/.yaml` 里的 `D:\`、`C:/` 之类绝对路径，发现即失败

## 目录结构

```
defect_manage/
├── defect/                  # 业务 app
│   ├── models.py            # DefectType / DefectRecord
│   ├── views.py             # 5 个 CRUD 视图
│   ├── forms.py             # DefectForm
│   ├── urls.py              # /defect/... 路由
│   ├── admin.py             # 后台注册
│   ├── migrations/          # 0001_initial
│   └── templates/defect/    # list / add / detail / edit / delete_confirm
├── defect_manage/           # 项目配置
│   ├── settings.py          # 环境变量驱动
│   ├── urls.py              # admin + defect + media
│   ├── asgi.py / wsgi.py
├── media/                   # 上传的图片(不进 git)
├── docs/                    # ADR 与使用手册
├── db.sqlite3               # 本地数据库(不进 git)
├── .env / .env.example      # 环境变量(前者不进 git)
└── requirements.txt
```

## 相关仓库

- [ODPlatform](https://github.com/chenkangkang999/ODPlatform) —— 目标检测开发平台
  （数据转换/质检/训练/推理）。本项目的检测图片原本由它的推理链路产出，
  两边的数据指纹与模型版本靠 `odp_meta` 对齐。

## 文档

- 架构决策记录：[`docs/adr/`](docs/adr/)
- 使用手册（面向使用者与运维）：[`docs/manual.md`](docs/manual.md)