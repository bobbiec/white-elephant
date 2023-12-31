import random
from itertools import permutations
from collections import namedtuple
from string import ascii_uppercase
from typing import List, Mapping
import csv
from tqdm import tqdm
from statistics import median

def dprint(*args, **kwargs):
    if False:
        print(*args, **kwargs)

class Gift:
    def __init__(self, name):
        self.name = name
        self.owner = None
        self.previous_owner = None
        self.steal_count = 0
        self.revealed = False

    def init_host(self, host):
        self.owner = host

    def take(self, new_owner):
        old_owner = self.owner
        if old_owner.name != 'host':
            self.steal_count += 1
            old_owner.chosen = None
            self.previous_owner = old_owner
        self.owner = new_owner
        return old_owner

    def __repr__(self):
        return f"Gift {self.name}"

Preferences = Mapping[Gift, int]

class WhiteElephant:
    def __init__(self, gifts: List[Gift], player_preferences: List[Preferences], last_steal_rule=False):
        self.host = Player(self, 'host', None)
        self.gifts = gifts
        for g in self.gifts:
            g.init_host(self.host)
        self.players = [Player(self, f"{i+1}", pref) for i, pref in enumerate(player_preferences)]
        self.last_steal_rule = last_steal_rule

    def play(self):
        player_stack = list(reversed(self.players))
        score = 0
        while len(player_stack) > 0:
            player = player_stack.pop()
            dprint(f"\n{player}'s turn!")
            stolen_player = player.take_turn()
            if stolen_player == self.host:
                dprint(f"  {player.name} reveals {player.chosen}")
                player.chosen.revealed = True
            else:
                dprint(f"  {player.name} steals {player.chosen} from {stolen_player.name} ({player.chosen.steal_count})")
                player_stack.append(stolen_player)
            new_score = self.score()
            dprint(f"  New score: {new_score} ({new_score - score:+})")
            score = new_score

        ## New rule: first player can steal at the end
        if self.last_steal_rule:
            player = self.players[0]
            dprint(f"\nL = Last round! {player} choosing")
            stolen_player = player.take_last_turn()
            if not stolen_player:
                dprint(f"  L = {player.name} keeps his own gift")
            else:
                dprint(f"  L = {player.name} steals {player.chosen} from {stolen_player.name} ({player.chosen.steal_count})")
                player_stack = [stolen_player]
                while len(player_stack) > 0:
                    player = player_stack.pop()
                    dprint(f"\nL = {player}'s turn!")
                    stolen_player = player.take_last_turn()
                    if stolen_player == None:
                        dprint(f"  L = {player} keeps his own gift")
                    else:
                        dprint(f"  L = {player.name} steals {player.chosen} from {stolen_player.name} ({player.chosen.steal_count})")
                        player_stack.append(stolen_player)
                    new_score = self.score()
                    dprint(f"  New score: {new_score} ({new_score - score:+})")
                    score = new_score

        dprint(f"Game over: {score}\n=========================")
        return Result([p.chosen for p in self.players], [p.score() for p in self.players], self.score())

    def score(self):
        return sum(p.score() for p in self.players)

class Player:
    def __init__(self, game: WhiteElephant, name: str, preferences: Preferences):
        self.name = name
        self.game = game
        self.preferences = preferences
        self.chosen = None

    def choose(self) -> Gift:
        visible_available = [g for g in self.game.gifts if g.steal_count < 3 and g.previous_owner != self and g.revealed]
        preferences = {
            gift: value
            for gift, value in self.preferences.items()
            if gift in visible_available
        }
        top_value = max(preferences.values() or [0])
        if top_value >= 50:
            choice = [gift for gift in preferences if preferences[gift] == top_value][0]
        else:
            # choose next unrevealed gift
            choice = [gift for gift in self.game.gifts if not gift.revealed][0]
        return choice

    def take(self, choice: Gift):
        stolen_from = choice.take(self)
        self.chosen = choice
        return stolen_from

    def take_turn(self):
        choice = self.choose()
        return self.take(choice)

    def swap(self, choice: Gift):
        # Note: I realized `take` is probably a specialization of `swap` when the current player has no gift.
        # Might be cleaner to combine them.
        old_chosen = self.chosen
        stolen_from = choice.take(self)
        self.chosen = choice
        stolen_from.chosen = old_chosen
        return stolen_from

    def take_last_turn(self):
        # special rules for the (first) last turn
        visible_available = [g for g in self.game.gifts if g.steal_count < 3 and g.previous_owner != self and g.revealed]
        preferences = {
            gift: value
            for gift, value in self.preferences.items()
            if gift in visible_available
        }
        top_value = max(preferences.values() or [0])
        current_value = self.preferences[self.chosen] if self.chosen else 0
        if top_value > current_value:
            choice = [gift for gift in preferences if preferences[gift] == top_value][0]
            return self.swap(choice)
        else:
            return None

    def score(self):
        return self.preferences.get(self.chosen, 0)

    def __repr__(self):
        return f"P{self.name}({self.chosen})"

Result = namedtuple('Result', ['assignment', 'score_parts', 'score'])

def bruteforce(gifts: List[Gift], player_preferences) -> List[Result]:
    seen = 0
    scores = []
    for assignment in permutations(gifts):
        score_parts = [player_preferences[person][gift] for person, gift in enumerate(assignment)]
        score = sum(score_parts)
        seen += 1
        scores.append(Result(assignment, score_parts, score))

    return list(sorted(scores, key=lambda r: r.score, reverse=True))

def is_pareto_optimal(result: Result, alternatives: List[Result]):
    # alternatives should be sorted already
    player_count = len(result.score_parts)

    for a in alternatives:
        if all(a.score_parts[i] > result.score_parts[i] for i in range(player_count)):
            return False
    return True

def got_top_n_choice(assignment, player_preferences, n=1):
    total = 0
    for person, gift in enumerate(assignment):
        prefs = player_preferences[person]  # dict of gift:value
        ranked_order = list(sorted(prefs.keys(), key=lambda g: prefs[g], reverse=True))
        if ranked_order.index(gift) < n:
            total += 1
    return total

def play_game(num_people, seed, csvwriter, last_steal_rule):
    random.seed(seed)
    gifts = [Gift(name) for name in ascii_uppercase[:num_people]]
    player_preferences: List[Preferences] = [{
        g: random.randint(0, 100)
        for g in gifts
    } for _ in range(num_people)]
    dprint(player_preferences)
    w = WhiteElephant(gifts, player_preferences, last_steal_rule)
    result = w.play()

    # Brute force "better" options (by sum of all preferences)
    top_scores = bruteforce(gifts, player_preferences)
    index = 0
    for i, r in enumerate(top_scores):
        if result.score >= r.score:
            index = i
            break

    p = len(top_scores)
    print(top_scores[0])
    print(top_scores[-1])
    pareto_result = is_pareto_optimal(result, top_scores[:index])

    data = {
        'seed': seed,
        'score': result.score,
        'rank': index + 1,
        'total_options': p,
        'percentile': (p-index) / p * 100,
        'best': top_scores[0].score,
        'percent_of_best': result.score / top_scores[0].score * 100,
        'average': median([a.score for a in top_scores]),
        'percent_of_average': result.score / median([a.score for a in top_scores]) * 100,
        'pareto_optimal': pareto_result,
        **{
            f'top_{n+1}': got_top_n_choice(result.assignment, player_preferences, n+1) for n in range(num_people)
        }
    }
    csvwriter.writerow(data)

    dprint(f"{seed}: {result.score}, rank {index+1} ({((p-index) / p * 100):2.3f} percentile); {result.score / top_scores[0].score * 100:2.0f}% of best {top_scores[0].score}; pareto-optimal: {pareto_result}; ", end="")
    dprint("; ".join(f"top-{n+1}: {got_top_n_choice(result.assignment, player_preferences, n+1)}" for n in range(num_people)))

def main(laststeal):
    for num_people in range(2, 10):
        dprint(f"\n{num_people} players:")
        with open(f'results-{num_people}{"-laststeal" if laststeal else ""}.csv', 'w', newline='') as csvfile:
            fieldnames = [
                'seed',
                'score',
                'rank',
                'total_options',
                'percentile',
                'best',
                'percent_of_best',
                'average',
                'percent_of_average',
                'pareto_optimal',
                *[f'top_{n+1}' for n in range(num_people)]
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for seed in tqdm(range(10000)):
                play_game(num_people, seed, writer, laststeal)

if __name__ == '__main__':
    main(True)
    main(False)
