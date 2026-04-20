# GLaDOS / Railgun 自动签到脚本

本项目是一个自动化每日签到脚本，支持 **GLaDOS** 及其迁移后的新站点 **Railgun**。通过每日自动签到获取点数和天数，从而实现账户的无缝续期。

本项目支持通过 **Github Actions** 或 **青龙面板** 部署，支持多账号运行，并集成了微信消息推送功能。

---

## 🌟 核心特性
- **双站支持**：同时包含 GLaDOS 与 Railgun 的自动签到脚本。
- **多账号支持**：支持配置多个账号的 Cookie，一键批量签到。
- **消息推送**：集成 PushPlus，签到结果每日自动推送至微信。
- **低成本维护**：完美适配 Github Actions 与青龙面板，一次配置，零成本自动运行。

---

## ⚙️ 环境变量配置 (Secrets)

无论你使用哪种部署方式，都需要在运行环境中配置以下变量：

| 变量名 | 是否必填 | 描述说明 |
| :--- | :---: | :--- |
| `GLADOS_COOKIE` | 是 (对GLaDOS) | 你的 GLaDOS 网页 Cookie。**多账号请用 `&` 隔开**（例：`cookie1&cookie2`）|
| `RAILGUN_COOKIE` | 是 (对Railgun) | 你的 Railgun 网页 Cookie。**多账号请用 `&` 隔开** |
| `PUSHPLUS_TOKEN` | 否 | PushPlus 微信推送凭证。如需推送，请前往 [PushPlus官网](https://www.pushplus.plus/) 获取并填写 |

---

## 🚀 部署与使用方法

### 方案一：使用 Github Actions (推荐，完全免费)

1. **Fork 本仓库**：点击页面右上角的 **Fork** 按钮，将项目复制到你的账号下。
2. **配置环境变量**：
   - 进入你 Fork 后的仓库，点击顶部菜单的 `Settings`。
   - 在左侧导航栏找到 `Secrets and variables` -> `Actions`。
   - 点击 `New repository secret`，依次添加上面表格中所需的变量名和你的对应值。
3. **配置工作流**：
   - 确保 `runGladosAction.yml` 文件位于 `.github/workflows/` 目录下（如果没有，请手动移动或创建）。
4. **激活并运行**：
   - 切换到仓库的 `Actions` 标签页，点击 `I understand my workflows, go ahead and enable them` 允许运行。
   - 回到仓库主页，点击右上角点亮 **Star (⭐)**，即可触发首次运行！
   - 之后 Actions 会按照设定的 Cron 时间每天定时为你自动签到。你可以在 `Actions` 页面查看每天的运行日志。

### 方案二：使用青龙面板

1. 打开你的青龙面板，进入 `脚本管理`。
2. 上传或新建脚本文件，将仓库中的 `glados.py`（或青龙专用版脚本）、`railgun.py` 内容复制进去。
3. 进入青龙面板的 `环境变量` 菜单，新建对应的环境变量（`GLADOS_COOKIE`、`RAILGUN_COOKIE`、`PUSHPLUS_TOKEN`）。
4. 进入 `定时任务` 菜单，新建任务：
   - 命令格式：`task glados.py` 或 `task railgun.py`
   - 定时规则：随意设置一个每天运行一次的 Cron 表达式（如 `0 8 * * *` 表示每天早上 8 点运行）。
5. 手动运行一次测试是否配置成功即可。

---

## 📌 致谢与声明

- 本项目基于原仓库 [lukesyy/glados_automation](https://github.com/lukesyy/glados_automation) 和 [domeniczz/GLaDOS_checkin_auto](https://github.com/domeniczz/GLaDOS_checkin_auto) 进行 Fork 及修改优化。
- **免责声明**：本项目仅供编程学习与日常自动化交流使用，请合理配置运行频率。切勿用于非法商业用途或对目标服务器造成恶意负担。
