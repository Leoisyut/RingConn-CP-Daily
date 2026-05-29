# RingWatch

RingWatch 是给 RingConn 产品团队使用的竞品动态 agent：每天搜索智能戒指竞品的新品、功能、App、传感器、订阅、渠道、合规和诉讼相关更新，去重后推送到飞书群。

## 当前竞品分层

截至 2026-05-29，建议先按三层监控：

| 层级 | 公司/品牌 | 核心产品 | 为什么要看 |
| --- | --- | --- | --- |
| 核心直接竞品 | Oura | Oura Ring 4、Oura App | 类目心智、睡眠/恢复算法、订阅模式和专利动作的标杆。 |
| 核心直接竞品 | Samsung | Galaxy Ring、Samsung Health | 手机生态入口强，AI 健康能力和无订阅策略会影响 Android 用户选择。 |
| 核心直接竞品 | Ultrahuman | Ring AIR、Ring Pro | 主打无订阅、代谢/运动人群，近年在美国销售和新品节奏上变化大。 |
| 重要直接竞品 | Circular | Circular Ring 2 | ECG/AFib、数字量戒和企业/临床 dashboard 是差异化信号。 |
| 重要直接竞品 | Amazfit / Zepp Health | Amazfit Helio Ring | 价格、运动生态和 Zepp App 体系，适合作为大众化/低价位参照。 |
| 重要直接竞品 | Movano Health | Evie Ring | 女性健康定位和医疗级传感方向，适合跟踪细分人群策略。 |
| 区域/价格竞品 | Noise、boAt、Luna、Rollme、COLMI、RENPHO | 多款智能戒指 | 印度、中国跨境和低价渠道会影响价格锚点、SKU 和功能下探。 |
| 邻近替代品 | Fitbit（Google）、Whoop、Garmin、Apple Watch、Samsung Watch | 平台/手环/运动表/健康表 | 这些平台的软件更新、订阅与算法会影响用户对健康洞察的预期。 |

详细监控配置在 `config/competitors.json`。

## 快速开始

```bash
python3 -m ringwatch list-competitors
python3 -m ringwatch run --dry-run
```

配置飞书：

```bash
cp .env.example .env
# 编辑 .env，填入 FEISHU_WEBHOOK_URL 和可选 FEISHU_WEBHOOK_SECRET
python3 -m ringwatch run
```

飞书群里添加「自定义机器人」后复制 webhook。建议在飞书机器人安全设置里开启「签名校验」，并把密钥填入 `FEISHU_WEBHOOK_SECRET`。

## 每日自动运行

### GitHub Actions

项目已内置 `.github/workflows/daily.yml`，默认配置为每天北京时间 09:00（UTC 01:00）运行。

注意：GitHub Actions 的 `schedule` 是 best-effort（不保证严格准点/不丢触发）。如果业务上必须“稳定在中国时间 09:00 触发”，建议使用「外部定时器」在 09:00 调用 GitHub API 触发 `workflow_dispatch`（下文提供示例）。

需要在仓库 Secrets 里添加：

| Secret | 必填 | 说明 |
| --- | --- | --- |
| `FEISHU_WEBHOOK_URL` | 是 | 飞书自定义机器人 webhook |
| `FEISHU_WEBHOOK_SECRET` | 否 | 飞书签名密钥 |

### 外部定时器触发（推荐更稳定）

用外部 cron（服务器/定时服务）在中国时间 09:00 调用 GitHub API，触发工作流的 `workflow_dispatch`：

- URL：`https://api.github.com/repos/<owner>/<repo>/actions/workflows/daily.yml/dispatches`
- Method：`POST`
- Headers：
  - `Authorization: token <GITHUB_TOKEN>`
  - `Accept: application/vnd.github+json`
  - `Content-Type: application/json`
- Body：`{"ref":"main"}`

`GITHUB_TOKEN` 建议使用 classic PAT（Tokens (classic)），并在 scopes 中勾选 `repo`（以及如页面可见则勾选 `workflow`）。

### 服务器 cron

```cron
0 9 * * * cd /path/to/ringwatch && /usr/bin/python3 -m ringwatch run >> .ringwatch/cron.log 2>&1
```

## 命令

```bash
python3 -m ringwatch run --dry-run          # 只打印，不推送，不写入已读状态
python3 -m ringwatch run --mark-seen        # dry-run 后也标记已读
python3 -m ringwatch run --lookback-days 3  # 只看最近 3 天
python3 -m ringwatch run --limit 20         # 最多推送 20 条
python3 -m ringwatch send-test              # 发送飞书连通性测试
```

## 信号口径

默认高优先级捕捉这些产品动态：

- 新品发布、预售、开卖、地区可用性变化。
- App、固件、算法、睡眠、HRV、SpO2、体温、EDA、ECG、AFib、血压、血糖等功能更新。
- 订阅、价格、捆绑、渠道、兼容性和生态联动。
- FDA、CE、临床、专利、ITC、进口禁令、授权和诉讼。
- 电池、充电盒、尺寸、材质、防水、佩戴舒适度等硬件变化。

状态文件默认保存在 `.ringwatch/state.json`，用于避免重复推送。

卡片与文本报告中的“生成时间”会按配置里的 `agent.timezone` 输出（默认 `Asia/Shanghai`），避免在 CI/服务器（通常是 UTC）上运行时显示错时区。
