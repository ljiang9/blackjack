# blackjack

终端二十一点小游戏：纯娱乐，不涉及任何真实货币。

## 玩法

```bash
python3 -m blackjack            # 交互模式：100 筹码开局
python3 -m blackjack --reset   # 筹码重置为 100
python3 -m blackjack --auto 1000 --seed 1   # 自动打 1000 局看统计
```

- 交互模式：每局输入下注额，然后 `h` 要牌 / `s` 停牌 / `d` 双倍（首两张牌可双倍）。
- 规则：庄家 17 点停牌（含软 17，即 A+6 也停牌）；Blackjack 赔 3:2；平局退注。
- 筹码保存在 `~/.config/blackjack.json`，下次打开继续。

## 设计取舍

- 随机牌堆用 `secrets.SystemRandom`（密码学安全随机）；`--auto` 加 `--seed` 时切换为可复现的 `random.Random`，**仅用于演示/验证**。
- 双倍只允许在首两张牌时使用；分牌（split）不在范围内——保持"小巧"定位。
- `--auto` 的基础策略很粗糙（<17 就要牌），真实基本策略表不在范围内。

## 已知局限

- 单副牌、无分牌、无保险（insurance）选项。
- 余额文件是本地 JSON 明文，别指望它防作弊——本来就是自己跟自己玩。
- 交互模式需要终端；管道/重定向下请用 `--auto`。

## 许可证

MIT，Copyright (c) 2026 ljiang9。娱乐项目，请勿用于赌博。
