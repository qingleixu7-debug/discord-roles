# Medeo Discord Roles

实时抓取 Medeo Discord 社区身份组分布的命令行工具。

通过 Discord Gateway WebSocket 协议拉取整个服务器的成员列表，按「用户加入目的 / 创作者职业类型 / 用户地域分布」三个维度聚合统计。

## 输出示例

```
====================================================
Medeo 身份组分布
统计时间: 2026-06-15T08:30:00+00:00
非 Bot 成员: 3,617
====================================================

【目的】共 1581 人次
  Explorer 探索者: 520 (33%)
  Growth-User 增长: 393 (25%)
  Monetization-Creator 变现: 402 (25%)
  Efficiency-User 效率: 144 (9%)
  Education-Creator 教育: 122 (8%)
  合计: 1581 ✅

【职业】共 1368 人次
  Influencer 网红/KOL: 454 (33%)
  ...

【地域】共 1520 人次
  ...
```

## 统计口径

- ❌ 排除 Bot 账号
- 同一用户持有多个身份组时，**分别计入各组**
- 同一组内**每人仅计一次**（已处理 `AI-Artist` 双 role ID 的去重）
- 各项人数加总 = 该组总人次（脚本输出末尾的 `✅` 即表示一致性校验通过）

## 安装

```bash
git clone https://github.com/<your-username>/medeo-discord-roles.git
cd medeo-discord-roles
pip install -r requirements.txt
```

## 配置

```bash
cp .env.example .env
# 编辑 .env，填入 DISCORD_USER_TOKEN
```

**Token 获取方式：**
1. 浏览器登录 Discord（不要用桌面客户端，桌面端会拦截开发者工具）
2. 按 `F12` 打开开发者工具 → Network 标签
3. 在 Discord 里切个频道，让 Network 抓到请求
4. 点击任意一条 `science` 或 `messages` 请求 → Headers → 复制 `authorization` 字段值

> ⚠️ **token 等同你的账号密码**。绝不要 commit 到 git，绝不要分享给别人。

## 使用

```bash
python fetch_roles.py
```

附加选项（通过环境变量）：

| 变量 | 说明 | 示例 |
|------|------|------|
| `DISCORD_USER_TOKEN` | **必填** Discord 用户 token | `<your_token>` |
| `HTTPS_PROXY` / `HTTP_PROXY` | 可选代理 | `http://127.0.0.1:7890` |
| `OUTPUT_JSON` | 可选 JSON 输出路径 | `output/roles.json` |

JSON 输出示例：

```json
{
  "fetched_at": "2026-06-15T08:30:00+00:00",
  "total_members": 3617,
  "groups": {
    "目的": {
      "Explorer 探索者": 520,
      "Growth-User 增长": 393,
      "...": 0
    },
    "职业": { "...": 0 },
    "地域": { "...": 0 }
  }
}
```

## 维护：身份组 ID 更新

如果 Medeo 服务器内重建了身份组（Discord role ID 会变），需要更新 [`config.py`](config.py) 的 `ROLE_MAP`。

获取最新角色 ID：在 Discord 客户端「设置 → 高级 → 开发者模式」开启后，右键服务器角色 → 复制角色 ID。

`AI-Artist` 当前因历史原因有两个 role ID（`1466704701742518313` 和 `1467264615762231450`），脚本会自动按用户去重，确保同一个人不会被算两次。

## 工作原理

Discord 的 REST API（`GET /guilds/{id}/members`）对**用户 token**返回 403，仅 Bot token 可用。本工具改走 Gateway WebSocket 协议：

1. 连接 `wss://gateway.discord.gg`，收到 `HELLO`（OP 10）后启动心跳线程
2. 发送 `IDENTIFY`（OP 2）完成认证
3. 收到 `READY`（事件）后发送 `REQUEST_GUILD_MEMBERS`（OP 8），`limit: 0` 表示全部
4. 接收 `GUILD_MEMBERS_CHUNK` 事件，按 chunk 聚合
5. 全部 chunk 完成后关闭连接、输出结果

每次尝试最多 120 秒；失败会自动重试，最多 3 次。

## 免责声明

本工具使用 Discord **用户 token** 抓取数据。Discord 的服务条款不建议自动化用户账号操作。本工具仅用于**社区运营者抓取自己社区的统计数据**，请勿用于其他用途。使用风险由你自行承担。

## License

MIT
