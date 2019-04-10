# -*- coding:utf-8 -*-
from tools import BET_AREA_LIST
# "bank", "player", "tie", "bankPair", "playerPair"
bet_dict = lambda: dict({"type": "bet", "data": {"area": '', "count": 0, "chipIndex": ''}})
card_dict = lambda: dict({"type": "cards", "data": {"bankCards": [], "playerCards": []}})
win_dict = lambda: dict({"type": "win", "data": {"winArea": [], 'score': 0, "count": 0, "playerPoints": 0}})
win_dict2 = {"type": "win", "data": [{"winArea": '', "score": 0, "count": 0}]}
status_dict = lambda: dict({"type": "status", "data": 1})
banker_info_dict = lambda: dict({"type": "banker", "data": {"playerName": '', "playerPoints": 0, "playerRemain": 0}})
error_dict = lambda: dict({"type": "error", "msg": ''})
recent_result = lambda: dict({"type": "result", "data": []})
bet_points_limit = lambda: dict({"type": "betLimit", "data": {"player": 0, "bank": 0, "tie": 0, "bankPair": 0, "playerPair": 0}})

BET_SUCCESS_CODE = 'bet'
BET_SUCCESS_MSG = {"type": "bet", "data": {}}

ERROR_MSG = {"type": "error", "msg": "失败原因"}

REGISTER_ERROR_INFO = u"注册失败，号码已经注册"
LOGIN_ERROR_INFO = u"用户名或密码错误，登陆失败。"
BET_ERROR_INFO = u"投注失败"
BET_POINTS_NOT_ENOUGH_INFO = u"分数不足， 投注失败。"
WEBSOCKET_ERROR_INFO = u"连接错误，无法建立连接。"
BANKER_ENOUGH = u"申请上庄失败，已经有超过10位庄家，请等待。"
TURN_BANKER_ERROR = u"申请上庄失败，分数不足或已经申请过。"
BEYOND_BET_LIMIT = u"超过了庄家投注限制或庄家已经封盘，暂时无法投注"
BANKER_CAN_NOT_BET = u"自己坐庄无法投注"
HAND_POINTS_NOT_ENOUGH_INFO = u"分数不足， 赠送失败。"
