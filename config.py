"""
Medeo Discord 服务器配置 & 身份组映射表

如果服务器的角色被重建（Discord role ID 会变），需要在 Discord 里通过
开发者模式右键复制角色 ID，然后更新下方的 ROLE_MAP。
"""

# Medeo AI 服务器 ID
GUILD_ID = "1347066703158181888"

# 身份组映射：role_id → (分组名, 显示名)
# 注意：AI-Artist 因历史原因有两个 role ID，归到同一逻辑组，
# 同一用户持有两个 ID 时只计一次（脚本内已做去重）。
ROLE_MAP = {
    # ── 用户加入目的 ──────────────────────────
    "1467265143359541319": ("目的", "Explorer 探索者"),
    "1467267392785874944": ("目的", "Growth-User 增长"),
    "1467267402025795584": ("目的", "Education-Creator 教育"),
    "1467267479280685246": ("目的", "Efficiency-User 效率"),
    "1467267507567071313": ("目的", "Monetization-Creator 变现"),

    # ── 创作者职业类型 ────────────────────────
    "1466704180335874121": ("职业", "Video-Pro 视频创作者"),
    "1466704492056674469": ("职业", "Marketing 营销"),
    "1466704558456573995": ("职业", "Educator 教育者"),
    "1466704574462300180": ("职业", "Influencer 网红/KOL"),
    "1466704701742518313": ("职业", "AI-Artist AI艺术家"),  # ID-A
    "1467264615762231450": ("职业", "AI-Artist AI艺术家"),  # ID-B (同一逻辑组)
    "1466704741588275261": ("职业", "Business-Owner 企业主"),

    # ── 用户地域分布 ──────────────────────────
    "1467270120090108125": ("地域", "North America 北美"),
    "1467270161546612927": ("地域", "Europe 欧洲"),
    "1467270211874062489": ("地域", "Latin America 拉美"),
    "1467270232887398421": ("地域", "South Asia 南亚"),
    "1467270289758093546": ("地域", "Southeast Asia 东南亚"),
    "1467270374763925586": ("地域", "East-Asia 东亚"),
    "1480593754506399887": ("地域", "Middle East 中东"),
    "1480593888824524820": ("地域", "Africa 非洲"),
    "1480593955786592448": ("地域", "Oceania 大洋洲"),
    "1480594018210549965": ("地域", "Russia/CIS"),
}

# 每组的展示顺序（不在此列表里的角色不会输出）
DISPLAY_ORDER = {
    "目的": [
        "Explorer 探索者",
        "Growth-User 增长",
        "Monetization-Creator 变现",
        "Efficiency-User 效率",
        "Education-Creator 教育",
    ],
    "职业": [
        "Influencer 网红/KOL",
        "Video-Pro 视频创作者",
        "AI-Artist AI艺术家",
        "Business-Owner 企业主",
        "Educator 教育者",
        "Marketing 营销",
    ],
    "地域": [
        "North America 北美",
        "Europe 欧洲",
        "East-Asia 东亚",
        "Africa 非洲",
        "South Asia 南亚",
        "Middle East 中东",
        "Southeast Asia 东南亚",
        "Latin America 拉美",
        "Russia/CIS",
        "Oceania 大洋洲",
    ],
}
