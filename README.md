# RingWatch

RingWatch 是给 RingConn 产品团队使用的竞品动态 agent：每天搜索智能戒指竞品的新品、功能、App、传感器、订阅、渠道、合规和诉讼相关更新，去重后推送到飞书群。

## 当前竞品分层

截至 2026-05-12，建议先按三层监控：

| 层级 | 公司/品牌 | 核心产品 | 为什么要看 |
| --- | --- | --- | --- |
| 核心直接竞品 | Oura | Oura Ring 4、Oura App | 类目心智、睡眠/恢复算法、订阅模式和专利动作的标杆。 |
| 核心直接竞品 | Samsung | Galaxy Ring、Samsung Health | 手机生态入口强，AI 健康能力和无订阅策略会影响 Android 用户选择。 |
| 核心直接竞品 | Ultrahuman | Ring AIR、Ring Pro | 主打无订阅、代谢/运动人群，近年在美国销售和新品节奏上变化大。 |
| 重要直接竞品 | Circular | Circular Ring 2 | ECG/AFib、数字量戒和企业/临床 dashboard 是差异化信号。 |
| 重要直接竞品 | Amazfit / Zepp Health | Amazfit Helio Ring | 价格、运动生态和 Zepp App 体系，适合作为大众化/低价位参照。 |
| 重要直接竞品 | Movano Health | Evie Ring | 女性健康定位和医疗级传感方向，适合跟踪细分人群策略。 |
| 区域/价格竞品 | Noise、boAt、Luna、Rollme、COLMI、RENPHO | 多款智能戒指 | 印度、中国跨境和低价渠道会影响价格锚点、SKU 和功能下探。 |
| 邻近替代品 | Whoop、Garmin、Apple Watch、Samsung Watch | 无屏手环/运动表/健康表 | 用户预算、恢复分、睡眠和订阅心智会被这些产品分流。 |

详细监控配置在 [config/competitors.json](/Users/bernicelay/Documents/New%20project/config/competitors.json)。

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

项目已内置 [.github/workflows/daily.yml](/Users/bernicelay/Documents/New%20project/.github/workflows/daily.yml)，默认每天北京时间 09:00 运行。

需要在仓库 Secrets 里添加：

| Secret | 必填 | 说明 |
| --- | --- | --- |
| `FEISHU_WEBHOOK_URL` | 是 | 飞书自定义机器人 webhook |
| `FEISHU_WEBHOOK_SECRET` | 否 | 飞书签名密钥 |

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
