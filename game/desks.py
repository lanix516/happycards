# -*- coding: utf-8 -*-
from tools import *
from cards import *
from player import Player
from message import *
import uuid
import random


class Desk:
    def __init__(self, desk_db):
        self.desk_id = desk_db.desk_id
        self.desk_url = "desk/"+self.desk_id
        self.deck = []
        self.players = []
        self.base_bet = 1
        self.all_bet = 0
        self.all_paid = 0
        self.bank_cards = []
        self.player_cards = []
        self.status = DESK_OPEN
        self.vip = False
        self.db = desk_db
        self.banks = []        # [{"player": player_obj, "remaining": 10}]
        self.bet_count = [0, 0, 0, 0, 0]

    def add_deck(self):
        self.deck = Deck()
        self.deck.shuffle()

    def is_player_in(self, player_id):
        for item in self.players:
            if item.id == player_id:
                return item
        else:
            return None

    def getUserByID(self, gameID):
        for item in self.players:
            if item.db.playerId == gameID:
                return item
        else:
            return None

    def getUserByName(self, name):
        for item in self.players:
            if item.name == name:
                return item
        else:
            return None

    def add_player(self, player):
        if isinstance(player, Player):
            item = self.is_player_in(player.id)
            if item:
                self.players.remove(item)
            self.players.append(player)
        else:
            raise ValueError

    def remove_player(self):
        for player in self.players:
            if player.left:
                player.ws = None
                player.desk = None
                player.left = False
                self.players.remove(player)

    def add_banker(self, player):
        if len(self.banks) >= 10:
            return BANKER_ENOUGH
        if isinstance(player, Player):
            banker_list = map(lambda x: x["player"], self.banks)
            if player not in banker_list and player.db.player_points > DESKER_POINTS:
                player_banker = {"player": player, "remaining": 10}
                self.banks.append(player_banker)
                res_list = []
                for item in self.banks:
                    res_list.append({"playerName": item["player"].name, "playerRemain": item["remaining"],
                                     "playerPoints": item["player"].db.player_points})
                player.send_message({"type": "bankerSucc","data": ""})
                self.send_message({"type": "bankerAll", "data": res_list})
                return None
            else:
                return TURN_BANKER_ERROR
        else:
            raise ValueError

    def banker_off(self, player):
        if isinstance(player, Player):
            for banker_item in self.banks:
                if banker_item['player'] is player:
                    banker_item['remaining'] = 0
                    return {"type": "bankerOff", "msg": u"申请下庄成功"}
            else:
                return {"type": "error", "msg": u"您尚未申请坐庄！"}
        else:
            raise ValueError

    def get_banker(self):
        if len(self.banks) > 0:
            return self.banks[0]
        return None

    def remove_banker(self):
        # 次数没了下庄， 分数不够下庄，这个地方一定会改
        res_dict = banker_info_dict()
        self.remove_little_points()
        if len(self.banks) > 0:
            now_player = self.banks[0]
            if now_player["remaining"] > 1:
                now_player["remaining"] -= 1
            else:
                del self.banks[0]

        if len(self.banks) > 0:
            now_player = self.banks[0]
            player_dict = {"playerName": now_player["player"].db.playerId, "playerRemain": now_player["remaining"],
                           "playerPoints": now_player["player"].db.player_points}
            self.send_message({"type": "banker", "data": player_dict})
        else:
            player_dict = {"playerName": "系统坐庄", "playerRemain": 100, "playerPoints": self.db.desk_points}
            self.send_message({"type": "banker", "data": player_dict})

        res_list = []
        for item in self.banks:
            res_list.append({"playerName": item["player"].name, "playerRemain": item["remaining"],
                             "playerPoints": item["player"].db.player_points})
        self.send_message({"type": "bankerAll", "data": res_list})

    def remove_little_points(self):
        for item in self.banks:
            if item["player"].db.player_points < DESKER_POINTS or item["player"].left:
                self.banks.remove(item)
            if item["remaining"] <= 1:
                self.banks.remove(item)

    def count_result_points(self):
        bet_list = self.bet_count
        ret_list = PAY_RET_LIST
        result_list = map(lambda x: x[0]*x[1], zip(bet_list, ret_list))
        return result_list

    def get_best_winner(self):
        # from collections import OrderedDict
        # od_list = OrderedDict()
        # result = [0, 1, 2]
        # new_list = result_list[0: 3]
        # max_index = new_list.index(max(new_list))
        # result.remove(max_index)
        unPair = True
        winner = 0
        try:
            desk_point = self.db.desk_points
        except:
            return winner, unPair
        result_list = self.count_result_points()
        new_list = []
        for pk, item in enumerate(result_list[0: 3]):
            if item < desk_point:
               new_list.append(pk)
        if new_list:
            winner = random.choice(new_list)
        else:
            winner = result_list.index(min(result_list[0: 3]))
        pair_score = result_list[3] + result_list[4]
        if pair_score < desk_point - result_list[winner]:
            unPair = False
        return winner, unPair

    def give_cards(self):
        winner, unPair = self.get_best_winner()
        gCount = 0
        while gCount < 8:
            gCount += 1
            self.bank_cards, self.player_cards = Deck.getCards(unPair=unPair)
            win_area = self.game_check()
            if winner == win_area:
                break
        return self.bank_cards, self.player_cards

    def check_cards_points(self):
        b_score = sum([item.rank for item in self.bank_cards if item.rank < 10]) % 10
        p_score = sum([item.rank for item in self.player_cards if item.rank < 10]) % 10
        return b_score, p_score

    def card_dict_list(self):
        b_cards = [card.getHex() for card in self.bank_cards]
        p_cards = [card.getHex() for card in self.player_cards]
        return {"bankCards": b_cards, "playerCards": p_cards}

    def check_pair_card(self, cards_list):
        b_list = [item.rank for item in cards_list]
        if len(b_list) != len(set(b_list)):
            return True
        else:
            return False

    def game_check(self):
        b_score, p_score = self.check_cards_points()
        if b_score > p_score:
            return BANK
        elif b_score == p_score:
            return TIE
        else:
            return PLAYER

    def send_message(self, message):
        error_dict = {"type": "error", "msg": ""}
        for player in self.players:
            if not hasattr(player, 'ws'):
                print "player hadnot ws"
            if not player.ws:
                print "player ws is none"
            if player.left:
                print player.name," player had left"

            if hasattr(player, 'ws') and player.ws and not player.left:
                    try:
                        player.send_message(message)
                    except IOError, e:
                        print str(e)
            else:
                error_dict["msg"] = WEBSOCKET_ERROR_INFO
                # print error_dict

    def get_bet_limit(self, area):
        banker_dict = self.get_banker()
        if banker_dict is None:
            return 1000000

        banker = banker_dict["player"]
        bet_list = []
        area_list = []
        if area < 3:
            bet_list.append(self.bet_count[3])
            area_list.append(PAY_RET_LIST[3])
            bet_list.append(self.bet_count[4])
            area_list.append(PAY_RET_LIST[4])
            bet_list.append(self.bet_count[area])
            area_list.append(PAY_RET_LIST[area])
        else:
            bet_list.append(self.bet_count[2])
            area_list.append(PAY_RET_LIST[2])
            bet_list.append(self.bet_count[area])
            area_list.append(PAY_RET_LIST[area])
        may_paid = reduce(lambda x, y: x+y, map(lambda x, y: x*y, bet_list, area_list))
        return banker.db.player_points - may_paid


if __name__ == "__main__":
    import os
    import pickle
    # new_desk = Desk()
    # with open("pkl/" + new_desk.desk_id+".pkl", "wb")as pkl_file:
    #         nd_pkl = pickle.dump(new_desk, pkl_file, True)

    pkl_files = os.listdir("pkl/")
    for i in pkl_files:
        f = open("pkl/"+i, "r")
        print f.name
        desk_item = pickle.load(f)
        print desk_item.desk_id
        f.close()