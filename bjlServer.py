# -*- coding:utf-8 -*-

from game.game import Game
from game.desks import Desk
from game.player import Player
from game.cards import *
import sys
sys.path.append('tornado')
import tornado.web
import tornado.websocket
import tornado.httpserver
import tornado.ioloop
import tornado.template
import os
import json
import cPickle as pickle
from game.message import *
from conn import *
import datetime
import time

# import redisco
# redisco.connection_setup(host='192.168.0.122', port=6379, db=2)

_game = Game()

users = {}
debug = False
default_desk = "1001"
# default_ip = "121.199.67.151"
default_ip = "172.20.85.1"

def paginator(query_set, page):
    page_count = 10
    res_set = query_set.limit(page_count*page, offset=(page-1)*page_count)
    return res_set


class BaseHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        # self.set_header("Access-Control-Allow-Origin", "http://121.199.67.151/")
        # self.set_header("Access-Control-Allow-Origin", "http://127.0.0.1")
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Credentials", "true")

    def get_current_user(self):
        return self.get_secure_cookie("user")

    def get_current_admin(self):
        return self.get_secure_cookie("admin")

    def get_current_admin_grade(self):
        return self.get_secure_cookie("admin_grade")


class RegisterHandler(BaseHandler):
    def get(self):
        self.write('<html><body><form action="/game/register" method="post">'
                   'phone: <input type="text" name="phone">'
                   'name: <input type="text" name="name">'
                   'password: <input type="text" name="password">'
                   '<input type="submit" value="register">'
                   '</form></body></html>')

    def post(self):
        res_dict = ERROR_MSG
        nextUrl = self.get_argument("next", " ")
        temp_list = nextUrl.split("/")
        desk_id_list = [item for item in temp_list if item.isdigit()]
        desk_id = desk_id_list[0] if desk_id_list else default_desk
        phone = self.get_argument("phone")
        name = self.get_argument("name")
        password = self.get_argument("password")
        query_set = PlayerModel.objects.filter(player_name=name)
        query_set_phone = PlayerModel.objects.filter(player_name=phone)

        if len(query_set) > 0 or len(query_set_phone) > 0:
            self.write({"type": "error", "msg": REGISTER_ERROR_INFO})
        else:
            player = PlayerModel(player_name=name, player_phone=phone, player_password=password, player_desk=desk_id)
            player.save()
            player.incr("player_points", 1000)
            player.update_attributes(playerId=unicode(100000+int(player.id)))
            player.save()
            self.set_secure_cookie("user", player.playerId)
            playerDict = player.attributes_dict
            playerDict["next"] = "desk/" + player.player_desk
            self.write({"type": "register", "data": playerDict})
            self.finish()


class AddNewPlayerHandler(BaseHandler):
    def get(self, *args, **kwargs):
        current_admin = self.get_current_admin()
        if not current_admin:
            self.redirect("/game/sitelogin")
        self.render("add_player.html", message=[])

    def post(self, *args, **kwargs):
        pid = self.get_argument("player_id", None)
        name = self.get_argument("player_name", None)
        phone = self.get_argument("player_phone", None)
        password = self.get_argument("player_password", None)
        message = []
        if not name:
            message.append("请输入用户名，此项不可为空")
        else:
            player_set = PlayerModel.objects.filter(player_name=name)
            if len(player_set) > 0:
                message.append("该用户名已经存在，请另选其他姓名。")
        if not password:
            message.append("请输入密码，此项不可为空")
        if not phone:
            message.append("请输入手机号，此项不可为空")
        if pid:
            if len(pid) < 6:
                message.append("id长度最少为6位")
            if not pid.isdigit():
                message.append("id必须为纯数字")
            player_set = PlayerModel.objects.filter(playerId=pid)
            if len(player_set) > 0:
                message.append("该id已经存在，请另选id")

        if len(message) > 0:
            return self.render("add_player.html", message=message)
        else:
            player = PlayerModel(player_name=name, player_phone=phone, player_password=password, player_desk=default_desk)
            player.save()
            if player:
                if pid:
                    player.update_attributes(playerId=pid)
                else:
                    player.update_attributes(playerId=unicode(100000+int(player.id)))
                player.incr("player_points", 100000)
                player.save()
            return self.redirect("/game/player")


class LoginHandler(BaseHandler):
    def get(self):
        desk_id = self.get_argument("next", "/")[5:]
        url = "http://{s_ip}?next={desk_id}".format(s_ip=default_ip, desk_id=desk_id)
        self.redirect(url)

    def post(self):
        name = self.get_argument("name")
        password = self.get_argument("password")
        redis_player = PlayerModel.objects.filter(player_name=name)
        if len(redis_player) > 0:
            player_item = redis_player.first()
            if player_item.player_password == password:
                self.set_secure_cookie("user", player_item.playerId, expires_days=None)
                users[id] = player_item
                playerDict = player_item.attributes_dict
                playerDict["next"] = "desk/"+player_item.player_desk
                player_json = json.dumps(playerDict)
                self.write(player_json)
                return self.finish()
            else:
                return self.write(json.dumps({"type": "error", "msg": LOGIN_ERROR_INFO}))
        else:
            return self.write(json.dumps({"type": "error", "msg": LOGIN_ERROR_INFO}))


class AdminSiteLoginHandler(BaseHandler):
    def get(self, *args, **kwargs):
        self.render("site_login.html")

    def post(self, *args, **kwargs):
        name = self.get_argument("admin_name")
        password = self.get_argument("admin_password")
        admin_set = PlayerModel.objects.filter(player_name=name)
        if len(admin_set) > 0:
            admin = admin_set.first()
            if admin.player_password == password:
                if admin.player_vip == 4:
                    self.set_secure_cookie("admin", name, expires_days=None)
                    self.set_secure_cookie("admin_grade", "4", expires_days=None)
                    return self.redirect("/game/siteindex")
                elif admin.player_vip > 0:
                    desk_db = DeskModel.objects.filter(desk_owner=admin.playerId).first()
                    if desk_db:
                        self.set_secure_cookie("admin_id", admin.playerId, expires_days=None)
                        self.set_secure_cookie("admin_grade", str(admin.player_vip), expires_days=None)
                        return self.redirect("/game/deskdetail/"+desk_db.id)
                    else:
                        return self.write("该账号无法登陆！")
                else:
                    return self.write("该账号无法登陆！")

            else:
                return self.write("用户名或密码错误， 无法登陆！")
        else:
            return self.write("用户名或密码不存在， 无法登陆！")


class AdminSiteIndexHandler(BaseHandler):
    def get(self, *args, **kwargs):

        current_admin = self.get_current_admin()
        if not current_admin:
            self.redirect("/game/sitelogin")

        res_dict = {"desk_count": 0, "player_count": 0}
        player_set = PlayerModel.objects.all()
        desk_set = DeskModel.objects.all()
        res_dict["desk_count"] = len(desk_set)
        res_dict["player_count"] = len(player_set)
        self.render("dash.html", result=res_dict)


class OpenDlHandler(BaseHandler):
    def get(self,id):
        desk_id = id
        url = "http://{s_ip}?next={desk_id}".format(s_ip=default_ip, desk_id=desk_id)
        self.redirect(url)

class OpenDeskHandler(BaseHandler):
    def get(self, *args, **kwargs):
        current_admin = self.get_current_admin()
        if not current_admin:
            self.redirect("/game/sitelogin")

        self.render("create_desk.html", message=[])

    def post(self, *args, **kwargs):
        global _game
        pid = self.get_argument('player_id', None)
        message = []
        if pid:
            player_set = PlayerModel.objects.filter(playerId=pid)
            if len(player_set) > 0:
                db_desk = DeskModel(desk_owner=pid)
                db_desk.save()
                db_desk.add_id()
                new_desk = Desk(db_desk)
                _game.add_desk(new_desk)
                application.add_handlers(r'.*$', [(r'/game/desk/' + new_desk.desk_id, GameDeskHandler, {'desk': new_desk})])

                player_item = player_set[0]
                player_item.player_desk = new_desk.desk_id
                if player_item.player_vip == 0:
                    player_item.player_vip = 1
                player_item.save()
            else:
                message.append(u"该Id玩家不存在，请输入正确的6位id")
                return self.render("create_desk.html", message=message)
        else:
            message.append(u"玩家Id不能为空，请输入玩家6位id")
            return self.render("create_desk.html", message=message)

        # with open("pkl/" + new_desk.desk_id+".pkl", "wb")as pkl_file:
        #     pickle.dump(new_desk, pkl_file)
        # new_desk.add_deck()
        return self.redirect("/game/deskdetail/" + db_desk.id)


class DeskListHandler(BaseHandler):
    def get(self, *args, **kwargs):
        current_admin = self.get_current_admin()
        if not current_admin:
            self.redirect("/game/sitelogin")

        desks = DeskModel.objects.all()
        self.render("desk_list.html", desks=desks)


class UpdateDeskHandler(BaseHandler):
    def get(self, desk_id):
        current_admin = self.get_current_admin()
        if not current_admin:
            self.redirect("/game/sitelogin")

        desk_db = DeskModel.objects.get_by_id(desk_id)
        return self.render("update_desk.html", desk=desk_db)

    def post(self, *args, **kwargs):
        desk_id = self.get_argument("desk_id")
        desk_points = self.get_argument("desk_points")
        desk_db = DeskModel.objects.get_by_id(desk_id)
        d_p = desk_db.desk_points

        desk_db.decr('desk_points', d_p)
        desk_db.incr('desk_points', desk_points)
        desk_db.save()
        self.redirect("/game/alldesk")


class DeskDetailHandler(BaseHandler):
    def get(self, desk_db_id):
        admin_grade = self.get_current_admin_grade()
        if not admin_grade:
            return self.redirect("/game/sitelogin")
        admin_grade = int(admin_grade)
        desk_db = DeskModel.objects.get_by_id(desk_db_id)
        player_list = PlayerModel.objects.filter(player_desk=desk_db.desk_id)
        if admin_grade < 4:
            current_admin = self.get_secure_cookie("admin_id")
            if desk_db.desk_owner != current_admin:
                return self.redirect("/game/sitelogin")
            else:
                return self.render("desk_detail.html", desk=desk_db, player_list=player_list, default_ip=default_ip)

        return self.render("desk_detail.html", desk=desk_db, player_list=player_list, default_ip=default_ip)


class DeskRecordHandler(BaseHandler):
    def get(self, desk_db_id):
        current_admin = self.get_current_admin()
        if not current_admin:
            self.redirect("/game/sitelogin")

        desk_db = DeskModel.objects.get_by_id(desk_db_id)
        record_list = GameModel.objects.filter(desk=desk_db.desk_id)

        self.render("desk_records.html", record_list=record_list)


class PlayerListHandler(BaseHandler):
    def get(self):
        current_admin = self.get_current_admin()
        if not current_admin:
            self.redirect("/game/sitelogin")

        page = self.get_argument("page", None)
        playerId = self.get_argument("playerId", None)
        player_list = PlayerModel.objects.all()
        page_all = len(player_list) / 10 + 1
        if page:
            player_list = paginator(player_list, int(page))
        if playerId:
            player_list = PlayerModel.objects.filter(playerId=playerId)
        self.render("players.html", players=player_list, page_all=range(1, page_all+1), player_record=[])


class PlayerRecordHandler(BaseHandler):
    def get(self, player_id):
        page = self.get_argument("page", None)
        player_db = PlayerModel.objects.get_by_id(player_id)
        record_list = PlayerDeskGame.objects.filter(player_id=player_db.id)
        page_all = len(record_list) / 10 + 1
        if page:
            record_list = paginator(record_list, int(page))
        self.render("players_record.html", player_record=record_list, page_all=range(1, page_all+1))


class UpdatePlayerHandler(BaseHandler):
    def get(self, player_id):
        current_admin = self.get_current_admin()
        if not current_admin:
            self.redirect("/game/sitelogin")

        player_db = PlayerModel.objects.get_by_id(player_id)
        return self.render("update_player.html", player=player_db)

    def post(self, *args, **kwargs):
        player_id = self.get_argument("player_id")
        player_vip = self.get_argument("player_vip")
        player_points = self.get_argument("player_points")

        player_db = PlayerModel.objects.get_by_id(player_id)
        if player_db:
            player_db.player_vip = int(player_vip)
            player_db.incr("player_points",int(player_points))
            player_db.save()

        self.redirect("/game/player")


class SearchPlayerHandler(BaseHandler):
    def post(self, *args, **kwargs):
        search_field = self.get_argument("search_field")
        search_type = self.get_argument("search_type", 1)
        search_type = int(search_type)
        if search_type == 1:
            search_set = PlayerModel.objects.filter(playerId=search_field)
        elif search_type == 2:
            search_set = PlayerModel.objects.filter(player_name=search_field)
        elif search_type == 3:
            search_set = PlayerModel.objects.filter(player_phone=search_field)
        self.render("players.html", players=search_set, page_all=range(1, 2), player_record=[])


class GameDetailHandler(BaseHandler):
    def get(self, gid):
        record_list = PlayerDeskGame.objects.filter(game_id=gid)
        self.render("game_detail.html", player_record=record_list)


class HandSelListHandler(BaseHandler):
    def get(self, *args, **kwargs):
        current_admin = self.get_current_admin()
        if not current_admin:
            self.redirect("/game/sitelogin")
        page = self.get_argument("page", None)
        query_set = HandSelModel.objects.all()
        page_all = len(query_set) / 10 + 1
        if page:
            query_set = paginator(query_set, int(page))
        self.render("handsel_list.html", hand_list=query_set, page_all=range(1, page_all+1))


class GameDeskHandler(BaseHandler):
    def __init__(self, *args, **kwargs):
        self.desk = kwargs['desk']
        super(GameDeskHandler, self).__init__(*args)

    @tornado.web.authenticated
    def get(self, *args, **kwargs):
        user_id = self.get_current_user()
        player_db = PlayerModel.objects.filter(playerId=user_id).first()
        player = self.desk.is_player_in(user_id)
        if player_db:
            if player:
                player.left = False
                player.desk = self.desk
            else:
                player = Player(user_id, player_db.player_name, player_db.player_phone, self.desk)

            player.db = player_db
            application.add_handlers(r'.*$', [(self.request.uri + '/' + str(player.id) + '/get', PokerWebSocket,
                                           {'player': player, 'desk': self.desk})])

            self.write(self.request.uri + '/' + str(player.id) + '/get')
            return self.finish()
        else:
            return self.write(self.request.uri)

class PlazaWebSocket(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        self.ws = self

    def on_message(self, message):
        #logon
        message = json.loads(message)
        if message["type"] == "logon":
            pass
        elif message["type"] == "create":
            #判断是否登录--重要
            res_mess = json.dumps({"msg": "123", "type": "roomID"})
            if self.ws is not None:
                try:
                    self.ws.write_message(res_mess)
                except:
                    print WEBSOCKET_ERROR_INFO
        elif message["type"] == "getRoom":
             #判断是否登录--重要

            #获取房间handler
            res_mess = json.dumps({"msg": "123", "type": "roomID"})
            if self.ws is not None:
                try:
                    self.ws.write_message(res_mess)
                except:
                    print WEBSOCKET_ERROR_INFO

    def on_close(self):
        print "left"

class PokerWebSocket(tornado.websocket.WebSocketHandler):
    def __init__(self, *args, **kwargs):
        self.player = kwargs.pop('player')
        self.desk = kwargs.pop('desk')
        self.player.ws = self
        self.player.desk = self.desk
        self.desk.add_player(self.player)

        super(PokerWebSocket, self).__init__(*args, **kwargs)

    def check_origin(self, origin):
        return True

    def open(self):
        self.player.ws = self

    def on_message(self, message):
        message = json.loads(message)
        if message["type"] == "mj":
            self.desk.send_message(message)
        if message["type"] == "bet":
            if _game.game_state == 0:
                bet_area = message["data"]["area"]
                bet_points = message["data"]["count"]
                res_message = self.player.bet_area(bet_area, bet_points)
                if not res_message:
                    res_bet = message
                    self.desk.send_message(res_bet)
                else:
                    self.player.send_message(res_message)
            else:
                self.player.send_message({"msg": BET_ERROR_INFO, "type": "error"})

        elif message["type"] == "banker":
            res_msg = self.desk.add_banker(self.player)
            if res_msg:
                self.player.send_message({"type": "error", "msg": res_msg})

        elif message["type"] == "handsel":
            rec_id = message["data"]["id"]
            rec_points = int(message["data"]["num"])
            hand_record = HandSelModel(sender=self.player.id, receiver=rec_id, points=rec_points)
            hand_record.save()
            try:
                rec_player = PlayerModel.objects.filter(playerId=rec_id).first()

                if rec_player is None:
                    self.player.send_message({"type": "handselerror", "data": u"对方不存在,请查证后重新输入"})
                    return

                # if rec_player.player_vip == 0 and self.player.db.player_vip == 0:
                #     self.player.send_message({"type": "handselerror", "data": u"权限不够无法赠送分数"})
                #     return

                if int(self.player.db.player_points) >= rec_points:
                    self.player.db.decr("player_points", rec_points)
                    rec_player.incr("player_points", rec_points)
                    hand_record.success = True

                    self.player.sendScore()
                    #发送赠送成功
                    sendSuccesMsg = u"支付人昵称:%s | 支付人ID:%s | 收款人昵称:%s | 收款人ID:%s | 转赠金额:%s | 日期:%s" % (self.player.name,str(self.player.id),rec_player.player_name,str(rec_player.playerId),str(rec_points),time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
                    # sendSuccesMsg = u"您的ID:%s 于 %s 赠送给 ID: %s 昵称为: %s %s 游戏币" % (str(self.player.id),time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),str(rec_id),rec_player.player_name,str(rec_points))
                    self.player.send_message({"type": "handsel", "data": sendSuccesMsg})

                    #通知接收成功
                    recUser = self.desk.getUserByID(rec_id)
                    if recUser:
                        recUser.sendScore()
                        recSuccesMsg = u"支付人昵称:%s | 支付人ID:%s | 收款人昵称:%s | 收款人ID:%s | 转赠金额:%s | 日期:%s" % (self.player.name,str(self.player.id),rec_player.player_name,str(rec_player.playerId),str(rec_points),time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
                        # recSuccesMsg = u"您的ID:%s 昵称为: %s 于 %s 接收到 ID: %s 赠送的 %s 游戏币" % (rec_id,rec_player.player_name,time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),str(self.player.id),str(rec_points))
                        recUser.send_message({"type": "handsel", "data": recSuccesMsg})
                else:
                    self.player.send_message({"type": "handselerror", "data": HAND_POINTS_NOT_ENOUGH_INFO})
            except Exception,e:
                self.player.send_message({"type": "error", "msg": u"操作错误"})
        elif message["type"] == "bankerOff":
            try:
                res_msg = self.desk.banker_off(self.player)
                self.player.send_message(res_msg)
            except:
                self.player.send_message({"type": "error", "msg": u"操作错误"})
        else:
            pass

    def on_close(self):
        print '%s left - removing them from the game' % self.player.name
        self.player.left = True
        try:
            del users[self.player.id]
            # self.desk.remove_player(self.player)  #不能直接删除，结算还需要用
        except KeyError:
            return

settings = {
    'static_path': os.path.join(os.path.realpath(__file__ + '/../'), 'static'),
    'template_path': os.path.join(os.path.realpath(__file__ + '/../'), 'static'),

    # 'template_path': os.path.join(os.path.realpath(__file__ + '/../'), 'I:/src/bjl'),
    'cookie_secret': 'QU%9B4\'?E$@(D0Q($5?@()".8B&%UOD1M5Y.IMD',
    'login_url': '/game/login',
    'auto_reload': True,
}
application = tornado.web.Application(**settings)
application.add_handlers('.*$', [
                                 (r'/game/register',RegisterHandler),
                                 (r'/game/login', LoginHandler),
                                 # admin site
                                 (r'/game/sitelogin', AdminSiteLoginHandler),
                                 (r'/game/siteindex', AdminSiteIndexHandler),
                                 (r'/game/alldesk', DeskListHandler),
                                 (r'/game/newdesk', OpenDeskHandler),
                                 (r'/game/addplayer', AddNewPlayerHandler),
                                 (r'/game/deskdetail/([0-9]+)', DeskDetailHandler),
                                 (r'/game/deskrecord/([0-9]+)', DeskRecordHandler),
                                 (r'/game/gamedetail/([0-9]+)', GameDetailHandler),
                                 (r'/game/handsel', HandSelListHandler),
                                 (r"/game/player", PlayerListHandler),
                                 (r'/game/playerrecord/([0-9]+)', PlayerRecordHandler),
                                 (r'/game/updateplayer', UpdatePlayerHandler),
                                 (r'/game/updateplayer/([0-9]+)', UpdatePlayerHandler),
								 (r'/game/updatedesk', UpdateDeskHandler),
                                 (r'/game/updatedesk/([0-9]+)', UpdateDeskHandler),
                                 (r'/g/([0-9]+)', OpenDlHandler),
                                 (r"/game/static/(.*)", tornado.web.StaticFileHandler, {"path": os.getcwd()+'/static'}),
                                 (r'/game/search', SearchPlayerHandler)
                                 # (r'/ws', PokerWebSocket),
])


# 恢复以前的所有桌子。桌子对象存在pkl目录下。可以删除文件去掉不想要的桌子。

desk_set = DeskModel.objects.all()
if len(desk_set) > 0:
    for item in desk_set:
        try:
            desk_item = Desk(item)
            _game.add_desk(desk_item)
            application.add_handlers(r'.*$', [(r'/game/desk/' + desk_item.desk_id, GameDeskHandler, {'desk': desk_item})])
        except Exception, e:
            print Exception
# pkl_files = os.listdir("pkl/")
# for i in pkl_files:
#     with open(''.join(["pkl/", i]), "r") as desk_file:
#         try:
#             desk_item = pickle.load(desk_file)
#             # desk_item.add_deck()
#             desk_item.bet_count = [0, 0, 0, 0, 0]
#             _game.add_desk(desk_item)
#             application.add_handlers(r'.*$', [(r'/game/desk/' + desk_item.desk_id, GameDeskHandler, {'desk': desk_item})])
#         except Exception, e:
#             print Exception


status = 0
scheduler = object()

def timeLoop():
    global _server
    global scheduler
    global status
    # _game.game_run()
    scheduler.stop()
    if status == 0:
        status = 1
        _game.game_reset()
        scheduler = tornado.ioloop.PeriodicCallback(timeLoop, 20*1000, io_loop=main_loop)
        scheduler.start()
    elif status == 1:
        status = 0
        _game.game_start()
        _game.game_close()

        scheduler = tornado.ioloop.PeriodicCallback(timeLoop, 15*1000, io_loop=main_loop)
        scheduler.start()


if __name__ == "__main__":
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8889)

    interval_ms = 10000
    main_loop = tornado.ioloop.IOLoop.instance()

    scheduler = tornado.ioloop.PeriodicCallback(timeLoop, 5*1000, io_loop=main_loop)
    scheduler.start()

    main_loop.start()
