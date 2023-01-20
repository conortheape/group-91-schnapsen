import random
from collections.abc import Iterable
from typing import Optional, Dict
from schnapsen.game import Bot, PlayerPerspective, Move, Card, GamePhase, Trump_Exchange, Marriage, RegularMove, SchnapsenTrickScorer
from schnapsen.deck import Suit, Rank


class StrategyBot1(Bot):
    def __init__(self, seed: int) -> None:
        self.seed = seed
        self.rng = random.Random(self.seed)

        self.aceWeight = 5
        self.tenWeight = 5
        self.jackWeight = 10
        self.kingWeight = 3
        self.queenWeight = 2

        self.trumpMultiplier = 0.8

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

        self.update_weights(state, leader_move)

        for move in moves:
            if isinstance(move, Trump_Exchange):
                self._print_stats(state, leader_move, move)
                self.numTricksPlayed += 1
                return move
            if isinstance(move, Marriage):
                self._fix_hands_after_marriage()
                self._print_stats(state, leader_move, move)
                self._fix_hands_after_marriage()
                self.numTricksPlayed += 1
                return move

        bestCards = []
        hand = self.runningHand.copy()
        for i in range(len(self.runningHand)):
            highestWeightCard = max(hand, key=hand.get)
            bestCards.append(highestWeightCard)
            del hand[highestWeightCard]

        for card in bestCards:
            if RegularMove(card) in moves:
                move = RegularMove(card)
                self._print_stats(state, leader_move, move)
                del self.runningHand[card]
                self.numTricksPlayed += 1
                return move

        print("this shouldn't print")
        print(f"weird move: {move}")
        self.numTricksPlayed += 1
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
        True if player has any marriages.
        """
        for card in self.runningHand.copy():
            if card.rank.value == 12:
                for card2 in self.runningHand.copy():
                    if card2.rank.value == 13 and card2.suit.value == card.suit.value:
                        self._separate_marriage(card, card2)
                        return True
        return False

    def update_weights(self, state, leader_move):

        # TODO: When not leader, moves that beat leader or low cards - increase weight
        # TODO: When not leader, if lead is trump, win if can otherwise discard low card
        # TODO: Other stuff too probably

        if state.get_phase() == GamePhase.ONE:
            # Base weights for general flow of game
            threshold = random.randint(4,6)
            if self.numTricksPlayed < threshold:
                self.aceWeight *= 1 + (self.numTricksPlayed / 20)
                self.tenWeight *= 1 + (self.numTricksPlayed / 18)
                self.jackWeight *= 1 + (self.numTricksPlayed / 16)
            else:
                self.aceWeight /= 1 + (self.numTricksPlayed / 16)
                self.tenWeight /= 1 + (self.numTricksPlayed / 16)
                self.jackWeight /= 1 + (self.numTricksPlayed / 16)

            self.kingWeight *= 1 + (self.numTricksPlayed / 22)
            self.queenWeight *= 1 + (self.numTricksPlayed / 22)

            # Value of weights based on score (high score leads to playing stronger cards to try win)
            myScore = state.get_my_score().direct_points + state.get_my_score().pending_points
            scoreThreshold = random.randint(40, 45)
            if myScore > scoreThreshold:
                self.aceWeight += (myScore / 4)
                self.tenWeight += (myScore / 4)
                self.trumpMultiplier += (myScore / 25)

            # If you have a royal and have seen its counterpart, its weight is increased (don't need to hold onto it)
            seenCards = state.seen_cards(leader_move).get_cards()
            for card in self.runningHand:
                if card.rank == Rank.QUEEN or card.rank == Rank.KING:
                    if self._get_counterpart(card) in self.runningHand:
                        self.runningHand[card] *= 2.2

            # Might get rid of this (if the leader card is a high card, increase trump multiplier).
            if leader_move:
                leaderCardPoints = SchnapsenTrickScorer.rank_to_points(SchnapsenTrickScorer(), leader_move.cards[0].rank)
                kingPoints = SchnapsenTrickScorer.rank_to_points(SchnapsenTrickScorer(), Rank.KING)
                if leaderCardPoints > kingPoints:
                    self.trumpMultiplier *= 1.2
            else:
                self.trumpMultiplier /= 1.2

            # Update weights of actual cards in running hand
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

                # Increase weight of card with higher rank as leader move of same suit
                if leader_move:
                    leaderCard = leader_move.cards[0]
                    if card.suit == leaderCard.suit and card.rank.value > leaderCard.rank.value:
                        self.runningHand[card] *= 1.5

                    # Increase weight of trumps if high non-trump card is played
                    leaderPoints = SchnapsenTrickScorer.rank_to_points(SchnapsenTrickScorer(), leaderCard.rank)
                    kingPoints = SchnapsenTrickScorer.rank_to_points(SchnapsenTrickScorer(), Rank.KING)
                    if leaderCard.suit != state.get_trump_suit() and card.suit == state.get_trump_suit() and leaderPoints > kingPoints:
                        self.runningHand[card] *= 1.5

                    # Decrease weight of higher cards if opponent leads a trump
                    cardPoints = SchnapsenTrickScorer.rank_to_points(SchnapsenTrickScorer(), card.rank)
                    queenPoints = SchnapsenTrickScorer.rank_to_points(SchnapsenTrickScorer(), Rank.QUEEN)
                    if cardPoints > queenPoints and leaderCard.suit == state.get_trump_suit():
                        self.runningHand[card] /= 1.5
        else:
            #################################################
            ###                CAREFUL:                   ###
            ###    BAD CODING PRACTICES PAST THIS POINT   ###
            #################################################

            opponentsHand = state.get_opponent_hand_in_phase_two().cards
            opponentNumTrumpCards = 0
            opponentHighestTrumpCardPoints = 0
            oPrevTrump = None
            for card in opponentsHand:
                if card.suit == state.get_trump_suit():
                    opponentNumTrumpCards += 1
                    if oPrevTrump is None:
                        opponentHighestTrumpCardPoints = SchnapsenTrickScorer.rank_to_points(SchnapsenTrickScorer(), card.rank)
                    elif SchnapsenTrickScorer.rank_to_points(SchnapsenTrickScorer(), card.rank) > SchnapsenTrickScorer.rank_to_points(SchnapsenTrickScorer(), oPrevTrump.rank):
                        opponentHighestTrumpCardPoints = SchnapsenTrickScorer.rank_to_points(SchnapsenTrickScorer(), card.rank)
                    oPrevTrump = card

            myNumTrumpCards = 0
            myHighestTrumpCardPoints = 0
            myPrevTrump = None
            for card in state.get_hand().cards:
                if card.suit == state.get_trump_suit():
                    myNumTrumpCards += 1
                    if myPrevTrump is None:
                        myHighestTrumpCardPoints = SchnapsenTrickScorer.rank_to_points(SchnapsenTrickScorer(), card.rank)
                    elif SchnapsenTrickScorer.rank_to_points(SchnapsenTrickScorer(), card.rank) > SchnapsenTrickScorer.rank_to_points(SchnapsenTrickScorer(), myPrevTrump.rank):
                        myHighestTrumpCardPoints = SchnapsenTrickScorer.rank_to_points(SchnapsenTrickScorer(), card.rank)
                    myPrevTrump = card

            if myNumTrumpCards > opponentNumTrumpCards or (myNumTrumpCards == opponentNumTrumpCards and myHighestTrumpCardPoints > opponentHighestTrumpCardPoints):
                for card in self.runningHand:
                    if card.suit == state.get_trump_suit():
                        self.runningHand[card] *= 2
                    else:
                        self.runningHand[card] /= 1.3
            else:
                opponentsSuits = []
                for card in opponentsHand:
                    if card.suit not in opponentsSuits:
                        opponentsSuits.append(card.suit)

                for card in self.runningHand:
                    if card.suit not in opponentsSuits and opponentNumTrumpCards > 0 and SchnapsenTrickScorer.rank_to_points(SchnapsenTrickScorer(), card.rank) < SchnapsenTrickScorer.rank_to_points(SchnapsenTrickScorer(), Rank.KING):
                        self.runningHand[card] *= 1.5
                    elif card.suit not in opponentsSuits and opponentNumTrumpCards < 1:
                        self.runningHand[card] *= 1.65



    def _print_stats(self, state, leader_move, move):
        print(f"true hand: {state.get_hand()}\n"
              f"runningHand: {self.runningHand}, length: {len(self.runningHand)}\n"
              f"marriageHand: {self.marriageHand}\n"
              f"leader move: {leader_move}\n"
              f"valid moves: {state.valid_moves()}\n"
              f"trump suit: {state.get_trump_suit()}\n"
              f"myScore: {state.get_my_score()}, opponent score {state.get_opponent_score()}\n"
              f"aceWeight: {self.aceWeight}\n"
              f"tenWeight: {self.tenWeight}\n"
              f"kingWeight: {self.kingWeight}\n"
              f"queenWeight: {self.queenWeight}\n"
              f"jackWeight: {self.jackWeight}\n"
              f"my move: {move}\n")

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

    def _separate_marriage(self, card1, card2):
        self.marriageHand[card1] = self.runningHand[card1]
        self.marriageHand[card2] = self.runningHand[card2]

    def __repr__(self) -> str:
        return f"StrategyBot1(seed={self.seed})"
