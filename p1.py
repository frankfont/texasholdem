import random

SUITS = {
    'Spades': '♠',
    'Clubs': '♣',
    'Hearts': '♥',
    'Diamonds': '♦'
}
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King', 'Ace']
BET_AMOUNTS = [5, 10, 25]

HAND_OPTIONS = [
    "High Card", "One Pair", "Two Pair", "Three of a Kind", "Straight",
    "Flush", "Full House", "Four of a Kind", "Straight Flush", "Royal Flush"
]

def create_deck():
    return [f"{rank} of {suit}" for suit in SUITS for rank in RANKS]

def shuffle_deck(deck):
    random.shuffle(deck)

def deal_cards(deck, count):
    return [deck.pop() for _ in range(count)]

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

def print_player_options(first_round, dealer_raised):
    print("\nYour Options:")
    if first_round:
        print("1. FOLD")
        print("2. BET (5, 10, 25)")
    else:
        print("1. FOLD")
        print("2. RAISE BET (5, 10, 25)")
        if dealer_raised:
            print("3. MATCH BET")
        else:
            print("3. TABLE-TAP")

def get_player_action(first_round, dealer_raised, dealer_bet):
    while True:
        choice = input("Enter your action (number): ").strip()
        if first_round:
            if choice == '1':
                return "FOLD", 0
            elif choice == '2':
                amt = input(f"Enter your bet amount {BET_AMOUNTS}: ")
                if amt.isdigit() and int(amt) in BET_AMOUNTS:
                    return "BET", int(amt)
        else:
            if choice == '1':
                return "FOLD", 0
            elif choice == '2':
                amt = input(f"Enter your raise amount {BET_AMOUNTS}: ")
                if amt.isdigit() and int(amt) in BET_AMOUNTS:
                    return "RAISE", int(amt)
            elif choice == '3':
                if dealer_raised:
                    return "MATCH", dealer_bet
                else:
                    return "TABLE-TAP", 0
        print("Invalid input.")

def choose_hand(player=True):
    label = "your" if player else "dealer's"
    print(f"\nSelect {label} best hand:")
    for i, hand in enumerate(HAND_OPTIONS, 1):
        print(f"{i}. {hand}")
    while True:
        try:
            choice = int(input(f"Enter the number corresponding to {label} hand: "))
            if 1 <= choice <= len(HAND_OPTIONS):
                return HAND_OPTIONS[choice - 1], choice
        except ValueError:
            pass
        print("Invalid input.")

def assess_hand(name, declared_rank, actual_rank):
    if declared_rank == actual_rank:
        print(f"✅ {name} correctly identified the best hand.")
    elif declared_rank > actual_rank:
        print(f"❌ {name} overestimated their hand.")
    else:
        print(f"❌ {name} underestimated their hand.")

def declare_winner(player_rank, dealer_rank):
    if player_rank > dealer_rank:
        print("\n🏆 PLAYER wins the game!")
    elif player_rank < dealer_rank:
        print("\n🏆 DEALER wins the game!")
    else:
        print("\n🤝 It's a TIE!")

def play_game():
    deck = create_deck()
    shuffle_deck(deck)

    print("\n=== New Game: Texas Hold'em ===")

    player_hand = deal_cards(deck, 2)
    dealer_hand = deal_cards(deck, 2)
    community_cards = deal_cards(deck, 5)
    revealed = []

    # print("\nYour hand:")
    # display_cards(player_hand)

    print("Dealer's hand: [FACE-DOWN] [FACE-DOWN]")

    pot = 0
    dealer_total = 0
    first_round = True
    dealer_raised = False
    dealer_last_bet = 0

    for round_index in range(5):
        if round_index == 3:
            print("\n--- Turn ---")
        elif round_index == 4:
            print("\n--- River ---")
        else:
            print(f"\n--- Flop card {round_index + 1} ---")

        # Show the player's hand on every round
        print("\nYour hand:")
        display_cards(player_hand)

        if not first_round:
            dealer_raised = random.choice([True, False])
            dealer_last_bet = random.choice(BET_AMOUNTS) if dealer_raised else 0
            if dealer_raised:
                print(f"\nDealer raises by ${dealer_last_bet}")
                pot += dealer_last_bet
                dealer_total += dealer_last_bet
            else:
                print("\nDealer checks (no raise)")

        print_player_options(first_round, dealer_raised)
        action, amount = get_player_action(first_round, dealer_raised, dealer_last_bet)
        if action == "FOLD":
            print("You folded. Dealer wins.")
            return
        elif action in ("BET", "RAISE", "MATCH"):
            pot += amount
        else:
            print("You table-tapped. No additional bet.")

        revealed.append(community_cards[round_index])

        print("\nCommunity Cards:")
        display_cards(community_cards, revealed_count=round_index + 1)

        first_round = False

    print("\n--- Final Reveal ---")
    print("Community Cards:")
    display_cards(community_cards)

    print("\nDealer's hand:")
    display_cards(dealer_hand)

    print("\nYour hand:")
    display_cards(player_hand)    

    print(f"\nTotal pot: ${pot}")

    player_hand_name, player_declared_rank = choose_hand(player=True)
    dealer_hand_name, dealer_declared_rank = choose_hand(player=False)

    print("\nNow enter the correct rankings to determine the real winner.")
    _, correct_player_rank = choose_hand(player=True)
    _, correct_dealer_rank = choose_hand(player=False)

    print("\n--- Hand Assessment ---")
    assess_hand("Player", player_declared_rank, correct_player_rank)
    assess_hand("Dealer", dealer_declared_rank, correct_dealer_rank)

    declare_winner(correct_player_rank, correct_dealer_rank)
    print("\n🎮 Game Over.")

def main():
    while True:
        play_game()
        again = input("\nPlay again? (y/n): ").strip().lower()
        if again != 'y':
            print("Thanks for playing!")
            break

if __name__ == "__main__":
    main()
