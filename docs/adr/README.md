# docs/adr —— 架构决策记录

存放本项目的 ADR（Architecture Decision Record）。一篇 ADR 只回答一个问题：
**当时为什么这么定、代价是什么、什么条件下该重新评估**。

命名：`ADR-<三位序号>-<短横线小写主题>.md`。写完不要改历史结论 —— 要推翻就新增一篇
并在旧的「状态」里标注 `Superseded by ADR-xxx`。

| 编号 | 主题 | 状态 |
|---|---|---|
| [ADR-001](ADR-001-tech-stack-and-layout.md) | 技术栈与服务端渲染的单体结构 | Accepted |
| [ADR-002](ADR-002-keep-drf-and-corsheaders.md) | 保留 DRF 与 corsheaders 依赖但仍走传统路由 | Accepted |
| [ADR-003](ADR-003-config-via-env.md) | 配置与密钥一律走环境变量，不硬编码 | Accepted |
| [ADR-004](ADR-004-media-storage.md) | 图片存储用 Django MEDIA_ROOT，不引入对象存储 | Accepted |