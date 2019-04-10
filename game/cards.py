# -*- coding:utf-8 -*-

import logging
import random
from tools import CARD_SUIT_DICT, CARD_SUIT_LIST



class Card:

    def __init__(self, suit=None, rank=None):
        assert suit is not None and rank is not None
        self.rank = rank
        self.suit = suit

    def __str__(self):
        return "[%s %s]" % (self.suit, self.rank)

    def getRank(self):
        return self.rank

    def getSuit(self):
        return self.suit

    def getHex(self):
        result = CARD_SUIT_DICT[self.suit] + self.rank
        return result

    def __eq__(self, other):
        if other is None:
            return False
        else:
            return self.rank == other.rank and self.suit == other.suit


class Deck:
    def __init__(self):
        self.cards = Deck.createDeck()

    @staticmethod
    def createDeck():
        values = range(1, 14)
        suits = ["SPADES", "CLUBS", "HEARTS", "DIAMONDS"]

        deck = []
        for value in values:
            for suit in suits:
                deck.append(Card(suit, value))
        return deck

    def sample(self, size):
        return random.sample(self.cards, size)

    def shuffle(self):
        random.shuffle(self.cards)

    def size(self):
        return len(self.cards)

    def removeCard(self):
        nextCard = self.cards.pop()
        return nextCard

    def removeCards(self, num=1):
        poppedElements = 0
        nextCards = []
        while poppedElements < num and self.hasNext():
            nextCard = self.cards.pop()
            nextCards.append(nextCard)
            poppedElements += 1
        return nextCards

    def hasNext(self):
        return len(self.cards) > 0

    @classmethod
    def makeOneCard(cls, rankList=None):
        suit = random.choice(CARD_SUIT_LIST)
        if not rankList:
            rankList = range(1, 14)
        rank = random.choice(rankList)
        card = Card(suit=suit, rank=rank)
        return card

    @classmethod
    def getCardsPoints(cls, cardList):
        cardPoints = sum([item.rank for item in cardList if item.rank < 10]) % 10
        return cardPoints


    @classmethod
    def getBaseCards(cls, unPair=True):
        cards_range = range(1, 14)
        cards = []
        while len(cards) < 2:
            card = cls.makeOneCard(cards_range)
            cards.append(card)
            if unPair:
                cards_range.remove(card.rank)
        return cards

    @classmethod
    def getCards(cls, unPair=True):
        player_cards = Deck.getBaseCards(unPair=unPair)
        banker_cards = Deck.getBaseCards(unPair=unPair)
        p_score = Deck.getCardsPoints(player_cards)
        b_score = Deck.getCardsPoints(banker_cards)

        if p_score < 6:
            if b_score < 8:
                player_cards.append(Deck.makeOneCard())
                player_third_cards = player_cards[2].rank
                p_score_after_drew = Deck.getCardsPoints(player_cards)
                if b_score == 7:
                        pass
                elif b_score == 6:
                    if player_third_cards in [6, 7]:
                        banker_cards.append(Deck.makeOneCard())
                elif b_score == 5:
                    if player_third_cards not in [1, 2, 3, 8, 9, 10]:
                        banker_cards.append(Deck.makeOneCard())
                elif b_score == 4:
                    if player_third_cards not in [1, 8, 9, 10]:
                        banker_cards.append(Deck.makeOneCard())
                elif b_score == 3:
                    if player_third_cards != 8:
                        banker_cards.append(Deck.makeOneCard())
                else:
                    banker_cards.append(Deck.makeOneCard())
        elif p_score > 7:  # 8, 9
            pass
        else:  # 6, 7
            if b_score < 6:
                banker_cards.append(Deck.makeOneCard())

        return banker_cards, player_cards

if __name__ == "__main__":
    a, b = Deck.getCards(True)
    print [a1.rank for a1 in a]
    print [a1.rank for a1 in b]
