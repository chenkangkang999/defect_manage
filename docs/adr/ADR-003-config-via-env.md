# ADR-003：配置与密钥一律走环境变量，不硬编码

| 项目 | 内容 |
|---|---|
| 状态 | ✅ Accepted |
| 决策日期 | 2026-10-24 |

## 背景

初始版本的 `settings.py` 里写死了 `SECRET_KEY = "django-insecure-=4n_$f!f..."`、
`DEBUG = True`、`ALLOWED_HOSTS = []`，并且把源码签进了 git。同时项目根存在一个 `.env`
（含 API Key），但**没有任何代码读它** —— 属于"看起来能配，实际是死配置"。

一次核查（22 个文件全扫）确认：本项目的路径写法是干净的，但密钥这一项违反了
"不硬编码"的要求。

## 备选方案

- 方案 A：引入 `python-dotenv` / `django-environ`，用成熟的库读 `.env`
- 方案 B：只用标准库写一个 10 行的 `.env` 读取函数（本决策）
- 方案 C：不读文件，要求一切通过真实环境变量传入

## 决定

方案 B：`settings.py` 顶部用标准库实现 `_load_env_file()`，把 `.env` 灌进 `os.environ`
（**已存在的真实环境变量优先，不会被文件覆盖**），随后所有敏感/可变配置都从环境变量读：

| 变量 | 默认值 | 说明 |
|---|---|---|
| `DJANGO_SECRET_KEY` | 无 → 生成一次性随机值并告警 | 生产必填 |
| `DJANGO_DEBUG` | `true` | 生产必须 `false` |
| `DJANGO_ALLOWED_HOSTS` | 空 | 逗号分隔 |
| `DJANGO_CORS_ALLOW_ALL` | `true` | 生产收紧 |
| `DJANGO_LANGUAGE_CODE` | `en-us` | 中文填 `zh-hans` |
| `DJANGO_TIME_ZONE` | `UTC` | 例如 `Asia/Shanghai` |

## 理由

1. **消除不可接受的硬编码**：密钥不再进仓库；换机器/换环境不需要改代码。
2. **不引入依赖**：`.env` 格式就 `KEY=value` 这一种用法，10 行标准库代码足够；
   少一个依赖就少一处版本冲突（这个项目已经因为与 ODPlatform 共用 venv 吃过亏）。
3. **优先级正确**：CI/容器里用真实环境变量，开发者本机用 `.env`，两者不冲突。
4. **开发体验不倒退**：没配 `DJANGO_SECRET_KEY` 也能起服务，只是密钥每次重启都变
   （登录态失效）并打印一条 `RuntimeWarning` —— 比直接崩掉更友好，又比默认写死更安全。

## 后果

- 正面：密钥、调试开关、主机名、跨域开关全部可配；`.env.example` 成为唯一配置说明书。
- 负面：`.env` 是多出来的一份本地状态，需要 `.gitignore` 保护（已忽略）且要提醒新人复制模板。
- 负面：开发环境不配密钥时"重启即掉登录态"，这是有意为之的提醒，不是 bug。
- 中性：`.env` 解析不支持多行值与变量展开；需要更复杂能力时再换方案 A。

## 撤销条件

- 需要多环境分层（dev/staging/prod 多份配置）或密钥托管（Vault/KMS）时，
  由新的配置方案 ADR 取代本篇；
- 若 `.env` 解析需求超出 `KEY=value`（多行、引用、展开），改用 `python-dotenv`。