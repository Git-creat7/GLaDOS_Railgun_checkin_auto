# GLaDOS / Railgun 自动签到脚本

本项目是一个自动化每日签到脚本，支持 **GLaDOS** (含 `glados.cloud`, `glados.rocks`, `glados.network`) 及其迁移后的新站点 **Railgun**。通过每日自动签到获取点数和天数，从而实现账户的无缝续期。

本项目支持通过 **Github Actions** 或 **青龙面板** 部署，支持多账号运行，并集成了微信消息推送功能。

---

## 🌟 核心特性
- **双站与多镜像支持**：同时包含 GLaDOS 与 Railgun 的自动签到脚本，GLaDOS 自动在 `glados.cloud`、`glados.rocks`、`glados.network` 镜像间故障切换。
- **适配 2026 最新认证**：适配 GLaDOS 新版会话格式 (`gld:sess` / `gld:sess.sig`) 及浏览器指纹 (Client Hints)。
- **多账号支持**：支持配置多个账号的 Cookie，一键批量签到（支持 `&` 或换行符分隔）。
- **消息推送**：集成 PushPlus，签到结果与错误诊断每日自动推送至微信。
- **自动兑换（可选）**：支持积分达标自动兑换会员天数。

---

## ⚙️ 环境变量配置 (Secrets)

无论你使用哪种部署方式，都需要在运行环境中配置以下变量：

| 变量名 | 是否必填 | 描述说明 |
| :--- | :---: | :--- |
| `GLADOS_COOKIE` | 是 (对GLaDOS) | 你的 GLaDOS 网页 Cookie。**必须包含 `gld:sess` 与 `gld:sess.sig`**。多账号请用 `&` 或换行符隔开 |
| `RAILGUN_COOKIE` | 是 (对Railgun) | 你的 Railgun 网页 Cookie。多账号请用 `&` 或换行符隔开 |
| `GLADOS_USER_AGENT` | 否 (推荐) | 导出 GLaDOS Cookie 时所用浏览器的 User-Agent，用于通过设备一致性校验 |
| `PUSHPLUS_TOKEN` | 否 | PushPlus 微信推送凭证。如需推送，请前往 [PushPlus官网](https://www.pushplus.plus/) 获取并填写 |
| `EXCHANGE_PLAN` | 否 | 积分自动兑换计划（可选：`plan500` 500分换100天，`plan200` 200分换30天，`plan100` 100分换10天，默认 `off`） |

> [!IMPORTANT]
> **关于 GLaDOS “没有权限”的排查说明**：
> 1. GLaDOS 进行了会话机制更新，旧版 `koa:sess` 已失效，必须使用包含 `gld:sess` 与 `gld:sess.sig` 的最新 Cookie。
> 2. 请在浏览器打开 [glados.cloud](https://glados.cloud) 重新登录，按 `F12` 打开开发者工具，在 `Network`（网络）标签页刷新页面，找到任意请求（如 `status` 或 `checkin`），复制 `Request Headers` 中的完整 `cookie`。
> 3. 更新 GitHub 仓库 `Settings -> Secrets and variables -> Actions` 中的 `GLADOS_COOKIE`。
> 4. 若提示设备不匹配 (`device-mismatch`)，请在同一个开发者工具的 Console 中执行 `navigator.userAgent`，并将输出的字符串添加到 Secrets 的 `GLADOS_USER_AGENT` 中。

---

## 🚀 部署与使用方法

### 方案一：使用 Github Actions (推荐，完全免费)

1. **Fork 本仓库**：点击页面右上角的 **Fork** 按钮，将项目复制到你的账号下。
2. **配置环境变量**：
   - 进入你 Fork 后的仓库，点击顶部菜单的 `Settings`。
   - 在左侧导航栏找到 `Secrets and variables` -> `Actions`。
   - 点击 `New repository secret`，依次添加上面表格中所需的变量名和对应值。
3. **配置工作流**：
   - 工作流文件位于 `.github/workflows/` 目录下（`runGladosAction.yml`、`runGladosNetworkAction.yml`、`runRailgunAction.yml`）。
4. **激活并运行**：
   - 切换到仓库的 `Actions` 标签页，点击 `I understand my workflows, go ahead and enable them` 允许运行。
   - 回到仓库主页，点击右上角点亮 **Star (⭐)** 或在 Actions 页面点击 `Run workflow` 手动触发首次运行。
   - 之后 Actions 会按照设定的 Cron 时间每天定时为你自动签到。

### 方案二：使用青龙面板

1. 打开你的青龙面板，进入 `脚本管理`。
2. 上传或新建脚本文件，将仓库中的 `glados.py`、`railgun.py` 内容复制进去。
3. 进入青龙面板的 `环境变量` 菜单，新建对应的环境变量（`GLADOS_COOKIE`、`RAILGUN_COOKIE`、`PUSHPLUS_TOKEN`、`GLADOS_USER_AGENT`）。
4. 进入 `定时任务` 菜单，新建任务：
   - 命令格式：`task glados.py` 或 `task railgun.py`
   - 定时规则：设置定时 Cron 表达式（如 `0 8 * * *` 表示每天早上 8 点运行）。
5. 手动运行一次测试是否配置成功即可。

---

## 📌 致谢与声明

- 本项目基于原仓库 [lukesyy/glados_automation](https://github.com/lukesyy/glados_automation) 和 [domeniczz/GLaDOS_checkin_auto](https://github.com/domeniczz/GLaDOS_checkin_auto) 进行 Fork 及修改优化。
- **免责声明**：本项目仅供编程学习与日常自动化交流使用，请合理配置运行频率。切勿用于非法商业用途或对目标服务器造成恶意负担。
