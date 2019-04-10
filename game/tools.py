# -*- coding: utf-8 -*-

BET_AREA_LIST = ["bank", "player", "tie", "bankPair", "playerPair"]
BET_AREA = lambda: dict.fromkeys(BET_AREA_LIST, 0)

CARD_SUIT_LIST = ["SPADES", "CLUBS", "HEARTS", "DIAMONDS"]
CARD_SUIT_DICT = {"SPADES": 0x10, "CLUBS": 0x20, "HEARTS": 0x30, "DIAMONDS": 0x40}

PAY_RET_LIST = [0.95, 1, 8, 11, 11]
BANK = 0
PLAYER = 1
TIE = 2
BANK_PAIR = 3
PLAYER_PAIR = 4
# BET STATE
BET_START = 0
BET_OVER = 1
# DESK_STATE
DESK_OPEN = 1
DESK_CLOSE = 0
# DESKER POINTS
DESKER_POINTS = 10000000
# GAME RET
GAME_RET = 0.95
# 枚举
def enum(**enums):
    return type('Enum', (), enums)