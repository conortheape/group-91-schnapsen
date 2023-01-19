import random
from collections.abc import Iterable
from typing import Optional, Dict
from schnapsen.game import Bot, PlayerPerspective, Move, Card, GamePhase, Trump_Exchange, Marriage, RegularMove
from schnapsen.deck import Suit, Rank


class StrategyBot1(Bot):
    def __init__(self, seed: int) -> None:
        self.seed = seed
        self.rng = random.Random(self.seed)

        self.aceWeight = 12
        self.tenWeight = 12
        self.jackWeight = 10
        self.kingWeight = 3
        self.queenWeight = 2

        self.trumpMultiplier = 3

        self.runningHand = {}
        self.marriageHand = {}

        self.seenClubsRoyal = False
        self.seenHeartsRoyal = False
        self.seenDiamondsRoyal = False
        self.seenSpadesRoyal = False

        self.numTricksPlayed = 0

    def get_move(self, state: PlayerPerspective, leader_move: Optional[Move]) -> Move:
        global action
        moves = state.valid_moves()
        self.update_hand(state.get_hand())
        hasMarriage = self.check_marriages(state, leader_move)

        print(self.runningHand)
        print(self.marriageHand)

        self.update_weights(state, leader_move)

        for move in moves:
            if isinstance(move, Trump_Exchange):
                print(move, "\n")
                return move
            if isinstance(move, Marriage):
                print(move, "\n")
                self._fix_hands_after_marriage()
                return move




        move = None
        for action in moves:
            if action.cards[0] in self.runningHand:
                move = action

        self.numTricksPlayed += 1
        del self.runningHand[move.cards[0]]
        print(move, "\n")
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
                        self._separate_marriage(card, card2)
                        return True

    def update_weights(self, state, leader_move):

        # TODO: When not leader, moves that beat leader or low cards - increase weight
        # TODO: When not leader, if lead is trump, win if can otherwise discard low card
        # TODO: Other stuff too probably

        # Base weights for general flow of game
        threshold = random.randint(4,6)
        if self.numTricksPlayed < threshold:
            self.aceWeight *= 1 + (self.numTricksPlayed / 18)
            self.tenWeight *= 1 + (self.numTricksPlayed / 15)
            self.jackWeight *= 1 + (self.numTricksPlayed / 12)
        else:
            self.aceWeight /= 1 + (self.numTricksPlayed / 10)
            self.tenWeight /= 1 + (self.numTricksPlayed / 10)
            self.jackWeight /= 1 + (self.numTricksPlayed / 10)

        self.kingWeight *= 1 + (self.numTricksPlayed / 20)
        self.queenWeight *= 1 + (self.numTricksPlayed / 20)

        # Value of weights based on score (high score leads to playing stronger cards to try win)
        myScore = state.get_my_score().direct_points + state.get_my_score().pending_points
        print(myScore)
        scoreThreshold = random.randint(40, 45)
        if myScore > scoreThreshold:
            self.aceWeight += (myScore / 2)
            self.tenWeight += (myScore / 2)
            self.trumpMultiplier += (myScore / 10)

        # If you have a royal and have seen its counterpart, its weight is increased (don't need to hold onto it)
        seenCards = state.seen_cards(leader_move).get_cards()
        for card in self.runningHand:
            if card.rank == Rank.QUEEN or card.rank == Rank.KING:
                if self._get_counterpart(card) in self.runningHand:
                    self.runningHand[card] = self.jackWeight

        # Update weights of actual cards in running hand #
        for card in self.runningHand:
            if card.rank == Rank.ACE:
                self.runningHand[card] = self.aceWeight
            if card.rank == Rank.TEN:
                self.runningHand[card] = self.tenWeight
            if card.rank == Rank.KING:
                self.runningHand[card] = self.kingWeight
            if card.rank == Rank.QUEEN:
                self.runningHand[card] = self.queenWeight
            if card.rank == Rank.JACK:
                self.runningHand[card] = self.jackWeight

            if card.suit == state.get_trump_suit():
                self.runningHand[card] *= self.trumpMultiplier


        print(self.numTricksPlayed)
        print(f"aceWeight: {self.aceWeight}\n"
              f"tenWeight: {self.tenWeight}\n"
              f"kingWeight: {self.kingWeight}\n"
              f"queenWeight: {self.queenWeight}\n"
              f"jackWeight: {self.jackWeight}")

    def _get_counterpart(self, card):
        if card.rank == Rank.QUEEN:
            return Card.get_card(Rank.KING, card.suit)
        if card.rank == Rank.KING:
            return Card.get_card(Rank.QUEEN, card.suit)

    def _fix_hands_after_marriage(self):
        for card in self.marriageHand:
            if card.rank == Rank.KING:
                self.runningHand[card] = self.marriageHand[card]
        self.marriageHand.clear()

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
