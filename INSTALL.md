# 节点引擎-人脉地图安装入口

https://raw.githubusercontent.com/xyxw1234-bot/节点引擎-人脉地图/main/SKILL.md

## 链接单独发送时的系统行为

用户不需要附加任何话术。只要把上面这条链接单独发给节点引擎 / Hermes，系统应自动完成以下判断：

1. 识别这是 raw GitHub SKILL.md 链接。
2. 读取 Skill frontmatter〔技能元数据〕并审查来源、名称、版本、权限边界和安全说明。
3. 如果本地未安装，进入安装流程。
4. 如果本地已安装，比较版本并检查更新。
5. 如果安全策略要求确认，只发一条极简确认卡片或短句。
6. 成功后只回复：人脉地图已安装。可试：打开我的人脉地图。

## 手动兜底命令

仅在自动识别能力未启用的老版本 Hermes 中使用：

```bash
hermes skills install https://raw.githubusercontent.com/xyxw1234-bot/节点引擎-人脉地图/main/SKILL.md
```


## 飞书原生卡片插件要求

只安装 Skill 文档只能让模型知道规则，不能保证飞书里出现真正可点击按钮。v2.1 必须同时安装并启用仓库内 companion 插件：

`plugins/relationship-map-feishu-card`

启用后，“打开人脉地图”会由插件直接发送飞书原生 `interactive` 卡片；没有插件时不得输出伪按钮。
