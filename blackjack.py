"""blackjack - 终端二十一点小游戏（娱乐，无真实货币）。"""

import argparse
import json
import os
import secrets
import sys

SUITS = ["♠", "♥", "♦", "♣"]
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
START_CHIPS = 100
BALANCE_FILE = os.path.join(os.path.expanduser("~"), ".config", "blackjack.json")


def new_deck(rng):
    deck = [(r, s) for s in SUITS for r in RANKS]
    rng.shuffle(deck)
    return deck


def hand_value(hand):
    """返回 (点数, 是否软牌)。A 按 11 算，爆了则逐个降为 1。"""
    total = 0
    aces = 0
    for rank, _ in hand:
        if rank == "A":
            aces += 1
            total += 11
        elif rank in ("J", "Q", "K"):
            total += 10
        else:
            total += int(rank)
    soft = aces > 0
    while total > 21 and aces:
        total -= 10
        aces -= 1
    if aces == 0:
        soft = False
    return total, soft


def show_hand(label, hand, hide_first=False):
    if hide_first:
        cards = ["??"] + [f"{r}{s}" for r, s in hand[1:]]
        print(f"  {label}：{' '.join(cards)}")
    else:
        cards = [f"{r}{s}" for r, s in hand]
        val, soft = hand_value(hand)
        tag = "（软）" if soft and val != 21 else ""
        print(f"  {label}：{' '.join(cards)}  = {val}{tag}")


def load_balance():
    try:
        with open(BALANCE_FILE, encoding="utf-8") as f:
            return int(json.load(f).get("chips", START_CHIPS))
    except (OSError, ValueError, KeyError):
        return START_CHIPS


def save_balance(chips):
    try:
        os.makedirs(os.path.dirname(BALANCE_FILE), exist_ok=True)
        with open(BALANCE_FILE, "w", encoding="utf-8") as f:
            json.dump({"chips": chips}, f)
    except OSError as e:
        print(f"警告：余额保存失败：{e}", file=sys.stderr)


def settle(player, dealer, bet):
    """返回玩家净收益（正=赢）。庄家 17 点停牌（含软 17）。"""
    pv, _ = hand_value(player)
    dv, _ = hand_value(dealer)
    p_bj = pv == 21 and len(player) == 2
    d_bj = dv == 21 and len(dealer) == 2
    if p_bj and d_bj:
        return 0
    if p_bj:
        return bet * 3 // 2  # blackjack 赔 3:2
    if d_bj:
        return -bet
    if pv > 21:
        return -bet
    if dv > 21:
        return bet
    if pv > dv:
        return bet
    if pv < dv:
        return -bet
    return 0


def play_hand(deck, bet, strategy=None, verbose=True):
    """打一手牌。strategy(hand, dealer_up) -> 'hit'/'stand'/'double'。返回净收益。"""
    player = [deck.pop(), deck.pop()]
    dealer = [deck.pop(), deck.pop()]
    if verbose:
        show_hand("你的牌", player)
        show_hand("庄家", dealer, hide_first=True)

    # 玩家回合
    doubled = False
    while True:
        pv, _ = hand_value(player)
        if pv >= 21:
            break
        if strategy:
            action = strategy(player, dealer[0])
        else:
            try:
                action = input("  要牌(h)/停牌(s)/双倍(d)？").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print()
                return None  # 用户退出
        if action in ("d", "double") and len(player) == 2 and not doubled:
            bet *= 2
            doubled = True
            player.append(deck.pop())
            if verbose:
                show_hand("你的牌", player)
            break
        elif action in ("h", "hit", "要牌"):
            player.append(deck.pop())
            if verbose:
                show_hand("你的牌", player)
        elif action in ("s", "stand", "停牌"):
            break
        else:
            if not strategy:
                print("  请输入 h / s / d。")

    # 庄家回合：17 点停牌（含软 17）
    while True:
        dv, _ = hand_value(dealer)
        if dv >= 17:
            break
        dealer.append(deck.pop())

    if verbose:
        show_hand("你的牌", player)
        show_hand("庄家", dealer)
    profit = settle(player, dealer, bet)
    if verbose:
        if profit > 0:
            print(f"  🎉 你赢了 {profit} 筹码！")
        elif profit < 0:
            print(f"  😞 输了 {-profit} 筹码。")
        else:
            print("  🤝 平局，退回注金。")
    return profit


def basic_strategy(hand, dealer_up):
    pv, _ = hand_value(hand)
    return "hit" if pv < 17 else "stand"


def cmd_auto(n, seed):
    import random
    rng = random.Random(seed) if seed is not None else secrets.SystemRandom()
    wins = losses = pushes = 0
    profit = 0
    for _ in range(n):
        deck = new_deck(rng)
        p = play_hand(deck, 10, strategy=basic_strategy, verbose=False)
        profit += p
        if p > 0:
            wins += 1
        elif p < 0:
            losses += 1
        else:
            pushes += 1
    print(f"共 {n} 局：赢 {wins} / 输 {losses} / 平 {pushes}")
    print(f"总盈亏：{profit} 筹码（每局下注 10）")
    print(f"玩家胜率：{wins / n * 100:.1f}%（庄家优势下应 < 50%）")
    return 0


def cmd_interactive():
    chips = load_balance()
    print("===== 终端二十一点 =====")
    print("娱乐小游戏，不涉及真实货币。庄家 17 点停牌（含软 17），Blackjack 赔 3:2。")
    print(f"当前筹码：{chips}（保存在 ~/.config/blackjack.json）")
    rng = secrets.SystemRandom()
    try:
        while chips > 0:
            try:
                raw = input(f"\n下注（1-{chips}，q 退出）：").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if raw in ("q", "quit", "退出"):
                break
            try:
                bet = int(raw)
            except ValueError:
                print("请输入数字。")
                continue
            if not 1 <= bet <= chips:
                print(f"下注须在 1–{chips} 之间。")
                continue
            chips -= bet
            deck = new_deck(rng)
            profit = play_hand(deck, bet)
            if profit is None:  # 用户中途退出
                chips += bet
                break
            chips += bet + profit
            save_balance(chips)
            print(f"当前筹码：{chips}")
            if chips <= 0:
                print("筹码输光了！用 --reset 可以重新开始（100 筹码）。")
    finally:
        save_balance(chips)
        print(f"\n最终筹码：{chips}。下次见！")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="blackjack", description="终端二十一点小游戏（娱乐，无真实货币）")
    ap.add_argument("--auto", type=int, metavar="N", help="非交互模式：自动打 N 局（基础策略）并统计")
    ap.add_argument("--seed", type=int, default=None, help="--auto 的随机种子（可复现）")
    ap.add_argument("--reset", action="store_true", help="重置筹码为 100 并退出")
    args = ap.parse_args(argv)
    if args.reset:
        save_balance(START_CHIPS)
        print(f"已重置：{START_CHIPS} 筹码。")
        return 0
    if args.auto is not None:
        if args.auto <= 0:
            print("error: --auto 须为正整数", file=sys.stderr)
            return 2
        return cmd_auto(args.auto, args.seed)
    return cmd_interactive()


if __name__ == "__main__":
    sys.exit(main())
