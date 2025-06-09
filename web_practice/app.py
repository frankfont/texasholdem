from flask import Flask, render_template, request, redirect, url_for, session
import random
from collections import Counter
import time

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this in production

SUITS = {
    'Spades': '♠',
    'Clubs': '♣',
    'Hearts': '♥',
    'Diamonds': '♦'
}
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King', 'Ace']
RANK_VALUES = {r: i for i, r in enumerate(RANKS, start=2)}
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
    return f"{rank}{SUITS[suit]}"

def simple_hand_explanation(guessed_rank, correct_rank):
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

def card_image_filename(card):
    rank, _, suit = card.partition(' of ')
    rank = rank.lower()
    suit = suit.lower()
    if rank == '10':
        rank = '10'
    elif rank == 'jack':
        rank = 'jack'
    elif rank == 'queen':
        rank = 'queen'
    elif rank == 'king':
        rank = 'king'
    elif rank == 'ace':
        rank = 'ace'
    # e.g. card_images/2_of_clubs.png -> static/card_images/2_of_clubs.png for url_for
    return f"card_images/{rank}_of_{suit}.png"

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'player_money' not in session:
        session['player_money'] = 100
        session['dealer_money'] = 100
    if request.method == 'POST':
        return redirect(url_for('new_round'))
    return render_template('index.html', player_money=session['player_money'], dealer_money=session['dealer_money'])

@app.route('/new_round', methods=['GET', 'POST'])
def new_round():
    deck = [f"{rank} of {suit}" for suit in SUITS for rank in RANKS]
    random.shuffle(deck)
    player_hand = [deck.pop(), deck.pop()]
    dealer_hand = [deck.pop(), deck.pop()]
    community_cards = [deck.pop() for _ in range(5)]
    session['player_hand'] = player_hand
    session['dealer_hand'] = dealer_hand
    session['community_cards'] = community_cards
    session['pot'] = 20
    session['player_money'] -= 10
    session['dealer_money'] -= 10
    return redirect(url_for('quiz'))

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    player_hand = session.get('player_hand')
    dealer_hand = session.get('dealer_hand')
    community_cards = session.get('community_cards')
    error = None
    # Initialize stats in session if not present
    if 'stats' not in session:
        session['stats'] = {
            'total_time_identify_hands': 0.0,
            'total_time_identify_winner': 0.0,
            'total_rounds': 0,
            'total_failed_hand_ids': 0,
            'total_failed_winner_ids': 0
        }
    import time
    if request.method == 'POST':
        # Use hidden fields to pass start times from the form
        start_hand_time = float(request.form['start_hand_time'])
        start_winner_time = float(request.form['start_winner_time'])
        hand_id_time = time.time() - start_hand_time
        winner_id_time = time.time() - start_winner_time
        player_guess = int(request.form['player_hand'])
        dealer_guess = int(request.form['dealer_hand'])
        winner_guess = request.form['winner']
        session['player_guess'] = player_guess
        session['dealer_guess'] = dealer_guess
        session['winner_guess'] = winner_guess
        session['hand_id_time'] = hand_id_time
        session['winner_id_time'] = winner_id_time
        return redirect(url_for('result'))
    # Pass card image filenames to the template
    player_hand_imgs = [card_image_filename(card) for card in player_hand]
    dealer_hand_imgs = [card_image_filename(card) for card in dealer_hand]
    community_card_imgs = [card_image_filename(card) for card in community_cards]
    return render_template('quiz.html',
        player_hand=player_hand,
        dealer_hand=dealer_hand,
        community_cards=community_cards,
        hand_options=HAND_OPTIONS,
        error=error,
        start_hand_time=time.time(),
        start_winner_time=time.time(),
        player_hand_imgs=player_hand_imgs,
        dealer_hand_imgs=dealer_hand_imgs,
        community_card_imgs=community_card_imgs
    )

@app.route('/result')
def result():
    player_hand = session.get('player_hand')
    dealer_hand = session.get('dealer_hand')
    community_cards = session.get('community_cards')
    player_guess = session.get('player_guess')
    dealer_guess = session.get('dealer_guess')
    winner_guess = session.get('winner_guess')
    pot = session.get('pot')
    player_money = session.get('player_money')
    dealer_money = session.get('dealer_money')

    player_best = evaluate_hand(player_hand + community_cards)
    dealer_best = evaluate_hand(dealer_hand + community_cards)
    actual_winner = compare_hands(player_best, dealer_best)

    player_correct = (player_guess == player_best[0])
    dealer_correct = (dealer_guess == dealer_best[0])
    winner_correct = (winner_guess == actual_winner)

    player_explanation = simple_hand_explanation(player_guess, player_best[0]) if not player_correct else ""
    dealer_explanation = simple_hand_explanation(dealer_guess, dealer_best[0]) if not dealer_correct else ""

    # Update money
    if actual_winner == "player":
        session['player_money'] += pot
    elif actual_winner == "dealer":
        session['dealer_money'] += pot
    else:
        session['player_money'] += pot // 2
        session['dealer_money'] += pot // 2

    hand_id_time = session.get('hand_id_time', 0.0)
    winner_id_time = session.get('winner_id_time', 0.0)
    stats = session.get('stats', {
        'total_time_identify_hands': 0.0,
        'total_time_identify_winner': 0.0,
        'total_rounds': 0,
        'total_failed_hand_ids': 0,
        'total_failed_winner_ids': 0
    })
    # Only update stats if this is a new round (not a page refresh)
    if hand_id_time > 0 or winner_id_time > 0:
        stats['total_time_identify_hands'] += hand_id_time
        stats['total_time_identify_winner'] += winner_id_time
        stats['total_rounds'] += 1
        failed_hand = 0
        failed_winner = 0
        if not player_correct:
            failed_hand += 1
        if not dealer_correct:
            failed_hand += 1
        if not winner_correct:
            failed_winner += 1
        stats['total_failed_hand_ids'] += failed_hand
        stats['total_failed_winner_ids'] += failed_winner
        session['stats'] = stats
    avg_hand_id_time = stats['total_time_identify_hands'] / stats['total_rounds'] if stats['total_rounds'] else 0
    avg_winner_id_time = stats['total_time_identify_winner'] / stats['total_rounds'] if stats['total_rounds'] else 0
    # Pass card image filenames to the template
    player_hand_imgs = [card_image_filename(card) for card in player_hand]
    dealer_hand_imgs = [card_image_filename(card) for card in dealer_hand]
    community_card_imgs = [card_image_filename(card) for card in community_cards]
    return render_template('result.html',
        player_hand=player_hand,
        dealer_hand=dealer_hand,
        community_cards=community_cards,
        hand_options=HAND_OPTIONS,
        player_guess=player_guess,
        dealer_guess=dealer_guess,
        winner_guess=winner_guess,
        player_best=player_best,
        dealer_best=dealer_best,
        actual_winner=actual_winner,
        player_correct=player_correct,
        dealer_correct=dealer_correct,
        winner_correct=winner_correct,
        player_explanation=player_explanation,
        dealer_explanation=dealer_explanation,
        player_money=session['player_money'],
        dealer_money=session['dealer_money'],
        hand_id_time=hand_id_time,
        winner_id_time=winner_id_time,
        avg_hand_id_time=avg_hand_id_time,
        avg_winner_id_time=avg_winner_id_time,
        total_hand_id_time=stats['total_time_identify_hands'],
        total_winner_id_time=stats['total_time_identify_winner'],
        total_rounds=stats['total_rounds'],
        total_failed_hand_ids=stats['total_failed_hand_ids'],
        total_failed_winner_ids=stats['total_failed_winner_ids'],
        player_hand_imgs=player_hand_imgs,
        dealer_hand_imgs=dealer_hand_imgs,
        community_card_imgs=community_card_imgs
    )

@app.route('/reset')
def reset():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
