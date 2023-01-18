import random
from collections.abc import Iterable
from typing import Optional, Dict
from schnapsen.game import Bot, PlayerPerspective, Move, Card



class StrategyBot1(Bot):
    def __init__(self, seed: int) -> None:
        self.seed = seed
        self.rng = random.Random(self.seed)

        self.aceWeight = 16
        self.tenWeight = 14
        self.jackWeight = 10
        self.kingWeight = 3
        self.queenWeight = 2
        self.trumpMultiplier = 5

        self.runningHand = {}
        self.marriageHand = {}

    def get_move(self, state: PlayerPerspective, leader_move: Optional[Move]) -> Move:
        global action
        self.update_hand(state.get_hand())
        self.check_marriages(state, leader_move)

        self.update_weights(state, leader_move)

        moves = state.valid_moves()
        move = None
        for action in moves:
            if action.cards[0] in self.runningHand:
                move = action

        del self.runningHand[move.cards[0]]
        return move



    def update_hand(self, hand):
        """
        Updates card-weight dictionary based on changes in new hand
        """
        for card in hand:
            if card not in self.runningHand:
                if card.rank.value == 1:
                    self.runningHand[card] = 16
                if card.rank.value == 10:
                    self.runningHand[card] = 14
                if card.rank.value == 11:
                    self.runningHand[card] = 10
                if card.rank.value == 13:
                    self.runningHand[card] = 3
                if card.rank.value == 12:
                    self.runningHand[card] = 2

    def check_marriages(self, state, leader_move):
        """
        Checks if the player has any marriages and separates them into a separate hand variable.
        """
        for card in self.runningHand.copy():
            if card.rank.value == 12:
                for card2 in self.runningHand.copy():
                    if card2.rank.value == 13 and card2.suit.value == card.suit.value:
                        if leader_move:
                            self._divide_marriage_weights(state, card, card2)
                            self._separate_marriage(card, card2)
                        else:
                            self._multiply_marriage_weights(state, card, card2)
                            self._separate_marriage(card, card2)

    def update_weights(self, state, leader_move):
        pass

    def _divide_marriage_weights(self, state, card1, card2):
        regularMarriageDivisor = 2
        royalMarriageDivisor = 3
        if card1.suit.value == state.get_trump_suit().value:
            self.runningHand[card1] /= royalMarriageDivisor
            self.runningHand[card2] /= royalMarriageDivisor
        else:
            self.runningHand[card1] /= regularMarriageDivisor
            self.runningHand[card2] /= regularMarriageDivisor

    def _multiply_marriage_weights(self, state, card1, card2):
        regularMarriageMultiplier = 4
        royalMarriageMultiplier = 5
        if card1.suit.value == state.get_trump_suit().value:
            self.runningHand[card1] /= royalMarriageMultiplier
            self.runningHand[card2] /= royalMarriageMultiplier
        else:
            self.runningHand[card1] /= regularMarriageMultiplier
            self.runningHand[card2] /= regularMarriageMultiplier

    def _separate_marriage(self, card1, card2):
        self.marriageHand[card1] = self.runningHand[card1]
        self.marriageHand[card2] = self.runningHand[card2]
        del self.runningHand[card1]
        del self.runningHand[card2]

    def __repr__(self) -> str:
        return f"StrategyBot1(seed={self.seed})"
