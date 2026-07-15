# 节点引擎人脉地图 Skill

这是面向企业老板和高管的“人脉地图”能力包。它支持自然对话记录关系，也支持用户发出“打开人脉地图 / 打开人脉库”时，以卡片列表方式浏览联系人。

## 关键设计

- 功能包与用户数据分离，更新 Skill 不覆盖用户联系人数据。
- 对话中提到某个人时，按正常上下文沟通、补全、确认、记录。
- 明确说“打开人脉地图 / 打开人脉库”时，进入可视化列表：每人只显示姓名与两行摘要，详情通过按钮进入二级页。
- 二级详情页在同一卡片框内切换，提供返回按钮回到列表。

## 安装

发布到 GitHub 后可安装：

```bash
hermes skills install https://raw.githubusercontent.com/<账号>/<仓库>/main/relationship-map/SKILL.md
```

当前为本地开发包，发布前需确认 GitHub 账号和仓库。


## Hermes 原生边界

本能力包必须跑在节点引擎 / Hermes 本身：作为独立 Skill 或后续插件安装。它不单独部署服务器，不要求外部数据库服务。SQLite 只是当前 Hermes profile 内部的数据保险箱文件。

默认数据位置：`$HERMES_HOME/data/relationship-map/`，没有 `HERMES_HOME` 时使用 `~/.hermes/data/relationship-map/`。


## 用户自定义扩展

用户安装后可以按自己的业务扩展字段、模块、指标和场景。推荐把自定义内容放到 `$HERMES_HOME/data/relationship-map/extensions/`，避免官方 Skill 更新时覆盖用户改动。


## 自适应关系维度

系统内置投资人、政府/协会、学校客户、渠道、专家、供应链等角色预设，但不会锁死。AI 会根据用户输入自动建议相应维度，用户可以确认、改名、删除或设为自己的默认规则。
