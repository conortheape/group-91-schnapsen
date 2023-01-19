import random
from collections.abc import Iterable
from typing import Optional, Dict
from schnapsen.game import Bot, PlayerPerspective, Move, Card, GamePhase
from schnapsen.deck import Suit, Rank


class StrategyBot1(Bot):
    def __init__(self, seed: int) -> None:
        self.seed = seed
        self.rng = random.Random(self.seed)

        self.aceWeight = 5
        self.tenWeight = 5
        self.jackWeight = 5
        self.kingWeight = 5
        self.queenWeight = 5

        self.runningHand = {}
        self.marriageHand = {}

        self.numTricksPlayed = 0

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

        self.numTricksPlayed += 1
        del self.runningHand[move.cards[0]]
        return move

    def update_hand(self, hand):
        """
        Updates card-weight dictionary based on changes in new hand
        """
        for card in hand:
            if card not in self.runningHand:
                if card.rank.value == 1:
                    self.runningHand[card] = self.aceWeight
                if card.rank.value == 10:
                    self.runningHand[card] = self.tenWeight
                if card.rank.value == 11:
                    self.runningHand[card] = self.jackWeight
                if card.rank.value == 13:
                    self.runningHand[card] = self.kingWeight
                if card.rank.value == 12:
                    self.runningHand[card] = self.queenWeight

    def check_marriages(self, state, leader_move):
        """
        Checks if the player has any marriages and separates them into a separate hand variable.
        """
        for card in self.runningHand.copy():
            if card.rank.value == 12:
                for card2 in self.runningHand.copy():
                    if card2.rank.value == 13 and card2.suit.value == card.suit.value:
                        if leader_move:
                            self._separate_marriage(card, card2)
                        else:
                            self._separate_marriage(card, card2)

    def update_weights(self, state, leader_move):
        print(self.aceWeight)

    def _set_trumpcards_weights(self, trumpSuit: Suit, influenceFactor: float) -> None:
        """
        Uses the trump suit to influence the weights of the trump cards in the running hand.
        influenceFactor: - is how much to divide by, + is how much to multiply by
        """
        if influenceFactor < 0:
            for card in self.runningHand:
                if card.suit == trumpSuit:
                    if card.rank == Rank.ACE:
                        self.runningHand[card] = self.aceWeight / abs(influenceFactor)
                    elif card.rank == Rank.TEN:
                        self.runningHand[card] = self.tenWeight / abs(influenceFactor)
                    elif card.rank == Rank.KING:
                        self.runningHand[card] = self.kingWeight / abs(influenceFactor)
                    elif card.rank == Rank.QUEEN:
                        self.runningHand[card] = self.queenWeight / abs(influenceFactor)
                    elif card.rank == Rank.JACK:
                        self.runningHand[card] = self.jackWeight / abs(influenceFactor)
        else:
            for card in self.runningHand:
                if card.suit == trumpSuit:
                    if card.rank == Rank.ACE:
                        self.runningHand[card] = self.aceWeight * abs(influenceFactor)
                    elif card.rank == Rank.TEN:
                        self.runningHand[card] = self.tenWeight * abs(influenceFactor)
                    elif card.rank == Rank.KING:
                        self.runningHand[card] = self.kingWeight * abs(influenceFactor)
                    elif card.rank == Rank.QUEEN:
                        self.runningHand[card] = self.queenWeight * abs(influenceFactor)
                    elif card.rank == Rank.JACK:
                        self.runningHand[card] = self.jackWeight * abs(influenceFactor)

    def _divide_marriage_weights(self, state, card1, card2):
        pass

    def _multiply_marriage_weights(self, state, card1, card2):
        pass

    def _separate_marriage(self, card1, card2):
        self.marriageHand[card1] = self.runningHand[card1]
        self.marriageHand[card2] = self.runningHand[card2]
        del self.runningHand[card1]
        del self.runningHand[card2]

    def __repr__(self) -> str:
        return f"StrategyBot1(seed={self.seed})"
