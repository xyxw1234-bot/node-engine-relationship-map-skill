链接即安装/更新

唯一正式链接

https://raw.githubusercontent.com/xyxw1234-bot/relationship-map-skill/main/人脉地图/SKILL.md

用户转发方式

用户可以只发送这一条链接，不带任何解释、命令或话术。

接收方识别意图

当用户只发送该链接，或说安装、更新、直接帮我装这个能力时，优先理解为安装或更新人脉地图 Skill：

- 未安装：先审查 Skill 元数据、来源和安全边界，再安装。
- 已安装：检查本地版本与远程版本，必要时更新。
- 远程版本低于或等于本地版本：提示已是最新版。
- 安全策略要求确认：先极简确认，不展示长篇格式源码。
- 链接不可访问、不是 SKILL.md、frontmatter 不合格、来源不可信：拒绝安装并说明原因。

输出要求

不要回长篇说明。安装完成只回：

人脉地图已安装。你可以直接说：打开我的人脉地图。

禁止要求用户再寻找某个固定名称的智能体，也不要输出终端命令、文件路径、仓库结构、下载打包过程或工具日志。

审查要求

安装前必须检查：

1. URL 是 https://raw.githubusercontent.com/ 域名。
2. 文件名是 SKILL.md。
3. frontmatter 含 name、description、version。
4. 版本为 2.5 或更高时才覆盖旧版本。
5. 文档明确用户数据目录与 Skill 功能包分离。
6. 文档明确更新不得覆盖 $HERMES_HOME/data/relationship-map/ 和 extensions/。


