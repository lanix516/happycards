# -*-coding:utf-8-*-

from tools import *
import json
from message import *


class Player:
    def __init__(self, pid, name, phone, desk):
        self.id = pid
        self.name = name
        self.phone = phone
        self.ws = None
        self.desk = desk
        self.db = None
        self.new_score = 0
        self.old_score = 0
        self.new_bet = BET_AREA()
        self.old_bet = BET_AREA()
        self.points = 10000
        self.left = False

    def bet_area(self, area, point):
        error_dict = ERROR_MSG
        if self.desk is None or self.desk.status != DESK_OPEN:
            error_dict["msg"] = BET_ERROR_INFO
            return error_dict
        if self.left:
            error_dict["msg"] = BET_ERROR_INFO
            return error_dict

        banker = self.desk.get_banker()
        if banker is not None and banker["player"] is self:
            error_dict["msg"] = BANKER_CAN_NOT_BET
            return error_dict

        if banker is not None and banker["player"].left:
            error_dict["msg"] = BEYOND_BET_LIMIT
            return error_dict

        point_limit = self.desk.get_bet_limit(area)
        if (PAY_RET_LIST[area] * point) > point_limit:
            error_dict["msg"] = BEYOND_BET_LIMIT
            return error_dict

        barea = BET_AREA_LIST[area]
        if barea in BET_AREA_LIST:
            if int(self.db.player_points) >= point:
                self.db.decr("player_points", point)
                self.db.save()
                self.new_bet[barea] += point
                self.desk.all_bet += point
                self.desk.bet_count[area] += point
                return None
            else:
                error_dict["msg"] = BET_POINTS_NOT_ENOUGH_INFO
                return error_dict
        else:
            raise ValueError

    def re_bet(self):
        self.old_bet = self.new_bet
        self.new_bet = BET_AREA()

    def sendScore(self):
        player_dict = {"playerPoints": self.db.player_points}
        self.send_message({"type": "updateScore", "data": player_dict})

    def send_message(self, message):
        error_dict = ERROR_MSG

        res_mess = json.dumps(message)
        if self.left:
            return
        if self.ws is not None:
            try:
                self.ws.write_message(res_mess)
            except:
                error_dict["msg"] = WEBSOCKET_ERROR_INFO
                print error_dict
        else:
            error_dict["msg"] = WEBSOCKET_ERROR_INFO
            print error_dict
