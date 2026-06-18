---
name: discord-roles
description: Fetch real-time identity group / role distribution from the Medeo AI Discord community. Use whenever the user asks for Medeo Discord 身份组分布 / role stats / community member breakdown, or wants to update the role-distribution section of a Medeo biweekly report.
---

# Medeo Discord 身份组实时抓取

通过 Discord Gateway WebSocket 协议，从 Medeo AI 服务器（guild `1347066703158181888`）实时拉取所有成员并按身份组聚合，输出「目的 / 职业 / 地域」三组人数和占比。

## 触发场景

- 用户说「统计/查/更新 Medeo 身份组分布」「身份组数据」「role distribution」
- 写 Medeo 双周报需要刷新「四、身份组分布」章节
- 任何需要 Medeo 当前 role 分布的快照

## 前置条件

skill 目录里必须能读到 `DISCORD_USER_TOKEN`。优先级：
1. 进程环境变量 `DISCORD_USER_TOKEN`
2. skill 目录下的 `.env` 文件

第一次使用前，确认两件事：
- `pip install -r requirements.txt`（依赖 `websocket-client` 和 `python-dotenv`）
- skill 目录下存在 `.env` 且包含 `DISCORD_USER_TOKEN=...`，否则提示用户复制 `.env.example` 并填入 token

token 获取方式见 [README.md](README.md)。

## 执行步骤

1. 切到 skill 所在目录（即本 `SKILL.md` 同级）
2. 运行：
   ```bash
   python fetch_roles.py
   ```
   如果用户机器需要代理（如 Clash），自动追加 `HTTPS_PROXY=http://127.0.0.1:7890`
3. 等待终端输出（典型 30–60 秒），脚本会打印「三组人数 + 合计 ✅」
4. 解析输出，**用 markdown 表格**回复用户，**保留每组合计行的 ✅ 校验标记**

## 输出格式（必须遵循）

```
**Medeo 身份组分布｜统计时间：<UTC 时间>｜非 Bot 成员：<数字>**

**用户加入目的（共 N 人次）**
| 身份组 | 人数 | 占比 |
| Explorer 探索者 | ... | ...% |
| ...
| **合计** | **N** | **100%** ✅ |

**创作者职业类型（共 N 人次）**
...

**用户地域分布（共 N 人次）**
...
```

按 Explorer / Influencer / North America 等固定显示顺序，参考 `config.py` 的 `DISPLAY_ORDER`。

## 失败处理

- **token 失效（401 / 拉取 0 人）**：提示用户更新 `.env` 里的 `DISCORD_USER_TOKEN`
- **三次重试都失败**：检查代理是否可用 / 网络连通性
- **某组合计 ❌**：脚本逻辑出错，**不要**自行修复数字，把原始输出贴给用户

## 不要做

- ❌ 不要硬编码 token 到任何文件
- ❌ 不要修改 `config.py` 里的 role ID 映射，除非用户明确说「身份组重建了」
- ❌ 不要把脚本输出截断，所有 22 个身份组都要显示（含 0 人的也算）
