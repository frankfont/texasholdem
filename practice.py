"""
Texas Hold'em Quiz Game

This program simulates hand ranking and winner selection via user input rather than automatic hand evaluation.

You are presented all the cards face-up,
yours and the dealer's and all the community cards.

Your job is to identify what hand you have and what hand the dealer has.
The program will correct you if wrong.

You and the dealer start with $100 each,
but in this practice game you will not practice the betting rounds part.

---
202506 - Frank Font created initial version
"""

import random
from collections import Counter
import time

SUITS = {
    'Spades': '♠',
    'Clubs': '♣',
    'Hearts': '♥',
    'Diamonds': '♦'
}
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King', 'Ace']
RANK_VALUES = {r: i for i, r in enumerate(RANKS, start=2)}
BET_AMOUNTS = [5, 10, 25]

HAND_OPTIONS = [
    "High Card", "One Pair", "Two Pair", "Three of a Kind", "Straight",
    "Flush", "Full House", "Four of a Kind", "Straight Flush", "Royal Flush"
]

def card_value(card):
    rank, _, suit = card.partition(" of ")
    return rank, suit

def rank_value(rank):
    return RANK_VALUES[rank]

def evaluate_hand(cards):
    ranks = []
    suits = []
    for card in cards:
        r, s = card_value(card)
        ranks.append(r)
        suits.append(s)
    rank_counts = Counter(ranks)
    suit_counts = Counter(suits)
    rank_nums = sorted([rank_value(r) for r in ranks], reverse=True)
    flush_suit = None
    for suit, count in suit_counts.items():
        if count >= 5:
            flush_suit = suit
            break
    flush_cards = []
    if flush_suit:
        flush_cards = [rank_value(r) for r, s in zip(ranks, suits) if s == flush_suit]
        flush_cards.sort(reverse=True)
    unique_rank_nums = sorted(set(rank_nums), reverse=True)

    def is_straight(vals):
        for i in range(len(vals) - 4):
            window = vals[i:i+5]
            if window[0] - window[4] == 4:
                return window[0]
        if set([14, 5, 4, 3, 2]).issubset(set(vals)):
            return 5
        return None

    straight_flush_high = None
    if flush_suit:
        sf_high = is_straight(flush_cards)
        if sf_high:
            straight_flush_high = sf_high

    fours = [r for r, c in rank_counts.items() if c == 4]
    threes = [r for r, c in rank_counts.items() if c == 3]
    pairs = [r for r, c in rank_counts.items() if c == 2]

    if straight_flush_high == 14:
        return (9, [14])
    if straight_flush_high:
        return (8, [straight_flush_high])
    if fours:
        quad_rank = max([rank_value(r) for r in fours])
        kickers = [r for r in rank_nums if r != quad_rank]
        return (7, [quad_rank] + kickers)
    if threes and (pairs or len(threes) > 1):
        trip_rank = max([rank_value(r) for r in threes])
        if len(threes) > 1:
            pair_rank = max([rank_value(r) for r in threes if rank_value(r) != trip_rank])
        else:
            pair_rank = max([rank_value(r) for r in pairs]) if pairs else 0
        return (6, [trip_rank, pair_rank])
    if flush_suit:
        top5 = flush_cards[:5]
        return (5, top5)
    straight_high = is_straight(unique_rank_nums)
    if straight_high:
        return (4, [straight_high])
    if threes:
        trip_rank = max([rank_value(r) for r in threes])
        kickers = [r for r in rank_nums if r != trip_rank][:2]
        return (3, [trip_rank] + kickers)
    if len(pairs) >= 2:
        top_pairs = sorted([rank_value(r) for r in pairs], reverse=True)[:2]
        kicker = max([r for r in rank_nums if r not in top_pairs])
        return (2, top_pairs + [kicker])
    if pairs:
        pair_rank = max([rank_value(r) for r in pairs])
        kickers = [r for r in rank_nums if r != pair_rank][:3]
        return (1, [pair_rank] + kickers)
    return (0, rank_nums[:5])

def hand_rank_name(rank_index):
    return HAND_OPTIONS[rank_index]

def compare_hands(player_hand_rank, dealer_hand_rank):
    if player_hand_rank[0] > dealer_hand_rank[0]:
        return "player"
    elif player_hand_rank[0] < dealer_hand_rank[0]:
        return "dealer"
    else:
        for p_val, d_val in zip(player_hand_rank[1], dealer_hand_rank[1]):
            if p_val > d_val:
                return "player"
            elif p_val < d_val:
                return "dealer"
        return "tie"

def format_card(card_str):
    rank, _, suit = card_str.partition(" of ")
    return f"[{rank}{SUITS[suit]}]"

def display_cards(cards, revealed_count=None):
    if revealed_count is None:
        revealed_count = len(cards)
    display = ""
    for i, card in enumerate(cards):
        if i < revealed_count:
            display += format_card(card) + " "
        else:
            display += "[FACE-DOWN] "
    print(display.strip())

def choose_hand(prompt):
    print(f"\n{prompt}")
    for i, hand in enumerate(HAND_OPTIONS, 1):
        print(f"{i}. {hand}")
    while True:
        try:
            choice = int(input("Enter the number corresponding to the hand: "))
            if 1 <= choice <= len(HAND_OPTIONS):
                return HAND_OPTIONS[choice - 1], choice - 1
        except ValueError:
            pass
        print("Invalid input.")

def choose_winner():
    print("\nWho won the game?")
    print("1. Player")
    print("2. Dealer")
    print("3. Tie")
    while True:
        choice = input("Enter winner (1/2/3): ").strip()
        if choice == '1':
            return "player"
        elif choice == '2':
            return "dealer"
        elif choice == '3':
            return "tie"
        else:
            print("Invalid input.")

def simple_hand_explanation(guessed_rank, correct_rank, cards):
    if guessed_rank == correct_rank:
        return ""
    if correct_rank > guessed_rank:
        if correct_rank == 3:
            return "There are three cards of the same rank, which makes Three of a Kind, stronger than what you guessed."
        if correct_rank == 1:
            return "There are two cards of the same rank, which is One Pair, better than what you guessed."
        if correct_rank == 2:
            return "There are two different pairs, which makes Two Pair, stronger than what you guessed."
        if correct_rank == 4:
            return "There are five cards in consecutive ranks, which makes a Straight, stronger than what you guessed."
        if correct_rank == 5:
            return "There are five cards of the same suit, which makes a Flush, stronger than what you guessed."
        if correct_rank == 6:
            return "There are a Three of a Kind plus a Pair, which makes a Full House, stronger than what you guessed."
        if correct_rank == 7:
            return "There are four cards of the same rank, which makes Four of a Kind, very strong."
        if correct_rank == 8:
            return "There are five cards in a row all of the same suit, which is a Straight Flush, very strong."
        if correct_rank == 9:
            return "This is the highest Straight Flush: Ten to Ace of the same suit, called Royal Flush."
    return f"The correct hand is {HAND_OPTIONS[correct_rank]}, which differs from your guess."

# Global accumulators for timing and rounds
_total_time_identify_hands = 0.0
_total_time_identify_winner = 0.0
_total_rounds = 0
_total_failed_hand_ids = 0
_total_failed_winner_ids = 0

def timed_choose_hand(prompt):
    start = time.time()
    result = choose_hand(prompt)
    elapsed = time.time() - start
    return result, elapsed

def timed_choose_winner():
    start = time.time()
    result = choose_winner()
    elapsed = time.time() - start
    return result, elapsed

def play_game(player_money, dealer_money):
    global _total_time_identify_hands, _total_time_identify_winner, _total_rounds, _total_failed_hand_ids, _total_failed_winner_ids
    deck = [f"{rank} of {suit}" for suit in SUITS for rank in RANKS]
    random.shuffle(deck)

    print("\n=== New Game: Texas Hold'em ===")

    player_hand = [deck.pop(), deck.pop()]
    dealer_hand = [deck.pop(), deck.pop()]
    community_cards = [deck.pop() for _ in range(5)]

    pot = 0
    bet = 10
    if player_money < bet:
        print("You do not have enough money to continue betting. Game over.")
        return player_money, dealer_money, False
    if dealer_money < bet:
        print("Dealer does not have enough money. You win!")
        return player_money + pot, dealer_money - pot, False

    player_money -= bet
    dealer_money -= bet
    pot += bet * 2

    print("\nCommunity Cards:")
    display_cards(community_cards)

    print("\nYour hand:")
    display_cards(player_hand)

    print("\nDealer's hand:")
    display_cards(dealer_hand)

    player_best = evaluate_hand(player_hand + community_cards)
    dealer_best = evaluate_hand(dealer_hand + community_cards)

    # Timed hand identification
    (player_declared_hand_name, player_declared_rank), hand_time1 = timed_choose_hand("Name your hand (pick from options):")
    (dealer_declared_hand_name, dealer_declared_rank), hand_time2 = timed_choose_hand("Name the dealer's hand (pick from options):")
    this_hand_id_time = hand_time1 + hand_time2
    _total_time_identify_hands += this_hand_id_time

    # Timed winner identification
    winner_guess, this_winner_id_time = timed_choose_winner()
    _total_time_identify_winner += this_winner_id_time

    _total_rounds += 1

    # --- Results ---
    print("\n--- Results ---")
    print(f"Your declared hand: {player_declared_hand_name}")
    print(f"Dealer's declared hand: {dealer_declared_hand_name}")
    print(f"Your guess for winner: {winner_guess.capitalize()}")

    print(f"\nCorrect player's hand: {hand_rank_name(player_best[0])}")
    print(f"Correct dealer's hand: {hand_rank_name(dealer_best[0])}")

    actual_winner = compare_hands(player_best, dealer_best)
    print(f"Actual winner: {actual_winner.capitalize()}")

    if player_declared_rank == player_best[0]:
        print("✅ You correctly identified your best hand.")
    else:
        print("❌ Your guess for your hand was incorrect.")
        explanation = simple_hand_explanation(player_declared_rank, player_best[0], player_hand + community_cards)
        if explanation:
            print("Explanation:", explanation)

    if dealer_declared_rank == dealer_best[0]:
        print("✅ You correctly identified the dealer's best hand.")
    else:
        print("❌ Your guess for the dealer's hand was incorrect.")
        explanation = simple_hand_explanation(dealer_declared_rank, dealer_best[0], dealer_hand + community_cards)
        if explanation:
            print("Explanation:", explanation)

    if winner_guess == actual_winner:
        print("✅ You correctly identified the winner!")
    else:
        print("❌ Your guess for the winner was incorrect.")

    if actual_winner == "player":
        player_money += pot
        print(f"\nYou win ${pot}! Your total money: ${player_money}")
        print(f"Dealer's money: ${dealer_money}")
    elif actual_winner == "dealer":
        dealer_money += pot
        print(f"\nDealer wins ${pot}. Your total money: ${player_money}")
        print(f"Dealer's money: ${dealer_money}")
    else:
        player_money += pot // 2
        dealer_money += pot // 2
        print(f"\nIt's a tie! Pot split. Your total money: ${player_money}")
        print(f"Dealer's money: ${dealer_money}")

    if player_money <= 0:
        print("\nYou've lost all your money! Game over.")
        return player_money, dealer_money, False

    # Count failed guesses for this round
    failed_hand = 0
    failed_winner = 0
    if player_declared_rank != player_best[0]:
        failed_hand += 1
    if dealer_declared_rank != dealer_best[0]:
        failed_hand += 1
    if winner_guess != actual_winner:
        failed_winner += 1
    _total_failed_hand_ids += failed_hand
    _total_failed_winner_ids += failed_winner

    # --- Statistics Table ---
    avg_hand_id_time = _total_time_identify_hands / _total_rounds if _total_rounds else 0
    avg_winner_id_time = _total_time_identify_winner / _total_rounds if _total_rounds else 0
    print("\n+-------------------+------------+------------+")
    print("|                   |  ID Hands  | ID Winner  |")
    print("+-------------------+------------+------------+")
    print(f"| This Round:       |  {this_hand_id_time:6.1f}s  |  {this_winner_id_time:6.1f}s  |")
    print(f"| Average Time:     |  {avg_hand_id_time:6.1f}s  |  {avg_winner_id_time:6.1f}s  |")
    print(f"| Total Time:       |  {_total_time_identify_hands:6.1f}s  |  {_total_time_identify_winner:6.1f}s  |")
    print("+-------------------+------------+------------+")
    print(f"Total Rounds: {_total_rounds} Total Failed Hand IDs: {_total_failed_hand_ids} Total Failed Winner IDs: {_total_failed_winner_ids}")

    return player_money, dealer_money, True

def main():
    player_money = 100
    dealer_money = 100

    print("\n###############################################\nWelcome to Texas Hold'em Quiz Game!")
    print("\nThis program will help you learn to identify the hands of the game.")
    print("\nYou are presented all the cards face-up,\nyours and the dealer's and all the community cards.")
    print("\nYour job is to identify what hand you have and what hand the dealer has.\nThe program will correct you if wrong.")
    print(f"\nYou and the dealer start with ${player_money} each,")
    print("but in this practice game you will not practice the betting rounds part.")

    while True:
        player_money, dealer_money, can_continue = play_game(player_money, dealer_money)
        if not can_continue:
            break
        cont = input("\nPlay another round? (y/n): ").strip().lower()
        if cont != 'y':
            break

if __name__ == "__main__":
    main()