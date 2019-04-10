# -*- coding:utf-8 -*-
from cards import Deck
from desks import Desk
from player import Player
from tools import *
from message import *
import json
from conn import *


class BaseGame(object):
    pass


class Game(BaseGame):
    def __init__(self):
        self.desks = []
        self.bank_cards = []
        self.player_cards = []
        self.game_state = 2
        self.deck = Deck()
        self.deck.shuffle()

    def add_desk(self, desk):
        if isinstance(desk, Desk):
            self.desks.append(desk)
        else:
            raise ValueError

    def del_desk(self, desk):
        try:
            self.desks.remove(desk)
            return True
        except ValueError:
            return False

    def game_start(self):
        if self.game_state == BET_START:
            self.game_state = BET_OVER
            bet_status = status_dict()
            bet_status["data"] = self.game_state
            for desk in self.desks:
                desk.give_cards()
                card_message = card_dict()
                card_message["data"] = desk.card_dict_list()
                desk.send_message(bet_status)
                desk.send_message(card_message)
        else:
            self.game_state = BET_START

    def game_close(self):
        for desk in self.desks:
            if desk.all_bet == 0:               # 没人下注这把就不记录
                continue
            finally_score = desk.game_check()
            result = win_dict()
            if desk.check_pair_card(desk.bank_cards):
                result["data"]["winArea"].append(BANK_PAIR)
            if desk.check_pair_card(desk.player_cards):
                result["data"]["winArea"].append(PLAYER_PAIR)
            if finally_score == BANK:
                result["data"]["winArea"].append(BANK)
            elif finally_score == TIE:
                result["data"]["winArea"].append(TIE)
            elif finally_score == PLAYER:
                result["data"]["winArea"].append(PLAYER)
            cards = desk.card_dict_list()
            win_area = result["data"]["winArea"]
            game_db = GameModel(desk=desk.desk_id, game_result=win_area, all_bet=desk.all_bet, bank_cards=cards["bankCards"], player_cards=cards["playerCards"])
            game_db.save()
            for player_item in desk.players:
                player_score = 0

                for item in win_area:
                    player_score += player_item.new_bet[BET_AREA_LIST[item]] * PAY_RET_LIST[item] + player_item.new_bet[BET_AREA_LIST[item]]
                player_final_score = int(player_score * GAME_RET)
                player_item.new_score = player_final_score
                player_item.db.incr("player_points", player_final_score)
                player_item.db.save()
                desk.all_paid += player_score
                result["data"]["score"] = player_final_score
                result["data"]["playerPoints"] = player_item.db.player_points
                player_item.send_message(result)
                # ============store in db==============
                try:
                    p_bet = BetModel(**player_item.new_bet)
                    p_bet.save()
                    pdg = PlayerDeskGame(player=player_item.db, desk=desk.desk_id, game=game_db, player_win=int(player_score),
                                         player_bet=p_bet, player_remind=int(player_item.db.player_points))
                    pdg.save()
                except:
                    pass
            game_db.all_paid = desk.all_paid
            desk_banker = desk.get_banker()
            finally_points = int(desk.all_bet - desk.all_paid)
            if desk_banker:
                desk_banker["player"].db.incr("player_points", finally_points)
                desk_banker["player"].sendScore()
                try:
                    b_bet = BetModel(bank=desk.bet_count[0], player=desk.bet_count[1], tie=desk.bet_count[2],
                                     bankPair=desk.bet_count[3], playerPair=desk.bet_count[4], )
                    b_bet.save()
                    pdg = PlayerDeskGame(player=desk_banker["player"].db, desk=desk.desk_id, game=game_db,
                                         player_win=finally_points, player_bet=b_bet, is_banker=True,
                                         player_remind=int(desk_banker["player"].db.player_points))
                    pdg.save()
                except:
                    pass
            else:
                desk.db.incr("desk_points", finally_points)
            desk.send_message({"type": "deskCount", "data": finally_points})

    def game_reset(self):
        self.game_state = BET_START
        bet_status = status_dict()
        bet_status["data"] = self.game_state
        res_dict = recent_result()
        for desk in self.desks:
            desk.all_bet = 0
            desk.all_paid = 0
            desk.remove_banker()
            desk.remove_player()
            desk.bet_count = [0, 0, 0, 0, 0]
            desk.send_message(bet_status)
            query_set = GameModel.objects.filter(desk=desk.desk_id).limit(20)
            result_list = [item.game_result for item in query_set]
            res_dict["data"] = result_list
            desk.send_message(res_dict)

            for player_item in desk.players:
                player_item.re_bet()

    def game_run(self):
        self.game_start()
        self.game_close()
        self.game_reset()
