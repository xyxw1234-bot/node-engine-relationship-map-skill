Hermes 原生运行边界

人脉地图不是独立服务器应用，不自建 SaaS 后端，不要求用户另配数据库服务。

运行位置

- 作为 Hermes Skill 或 Hermes 插件运行。
- 数据跟随当前 Hermes profile。
- 默认数据目录：`$HERMES_HOME/data/relationship-map/`。
- 无 `HERMES_HOME` 时：`~/.hermes/data/relationship-map/`。

更新边界

GitHub 只发布能力包文件：`SKILL.md`、`references/`、`templates/`、`examples/`、`scripts/`。

用户真实人脉数据不进入 GitHub，不放在 Skill 包目录里，不随 Skill 更新覆盖。

SQLite 的定位

SQLite 只是 Hermes profile 内部的本地数据文件，不是独立数据库服务器。

后续插件化

如果升级为 Hermes 插件，仍然复用同一数据目录和同一 profile 权限边界，只增加历史复杂方案复杂控件事件和更好的 UI 适配，不改变用户侧体验。



