# -*- coding:utf-8 -*-
import redis
import redisco

from redisco import models
redisco.connection_setup(host='127.0.0.1', port=6379, db=8)


class DeskModel(models.Model):
    desk_id = models.Attribute(unique=True)
    desk_owner = models.Attribute()
    desk_points = models.Counter()

    def add_id(self):
        self.desk_id = str(1000+int(self.id))
        self.save()


class PlayerModel(models.Model):
    playerId = models.Attribute()
    player_phone = models.Attribute(required=True)
    player_name = models.Attribute(required=True)
    player_password = models.Attribute()
    last_login = models.DateTimeField()
    player_points = models.Counter()
    player_vip = models.IntegerField(default=0)
    player_desk = models.Attribute()


class CardModel(models.Model):
    card_suit = models.Attribute()
    card_rank = models.IntegerField()


class BetModel(models.Model):
    bank = models.IntegerField()
    player = models.IntegerField()
    tie = models.IntegerField()
    bankPair = models.IntegerField()
    playerPair = models.IntegerField()


class GameModel(models.Model):
    desk = models.Attribute()
    game_time = models.DateTimeField(auto_now_add=True)
    all_bet = models.IntegerField(default=0)
    all_paid = models.IntegerField(default=0)
    game_result = models.ListField(int)
    bank_cards = models.ListField(int)
    player_cards = models.ListField(int)


class PlayerDeskGame(models.Model):
    desk = models.Attribute()
    player = models.ReferenceField(PlayerModel)
    game = models.ReferenceField(GameModel)
    player_bet = models.ReferenceField(BetModel)
    player_win = models.IntegerField()
    player_remind = models.IntegerField()
    is_banker = models.BooleanField(default=False)


class HandSelModel(models.Model):
    sender = models.Attribute()
    receiver = models.Attribute()
    points = models.IntegerField()
    date = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=False)


class AdminModel(models.Model):
    admin_name = models.Attribute(required=True, unique=True)
    admin_password = models.Attribute()
    admin_grade = models.IntegerField()


if __name__ == "__main__":
    player_set = PlayerModel.objects.filter(player_name="admin001")
    if len(player_set) > 0:
        player = player_set[0]
    else:
        player = PlayerModel(player_name="admin001", player_password="admin001", player_phone="admin001", playerId="100001", player_vip=4)
        player.save()
        player.incr("player_points", 1000000)

    desk_set = DeskModel.objects.filter(desk_id="1001")
    if len(desk_set) > 0:
        for item in desk_set:

            print item.id
    else:
        desk = DeskModel(desk_id="1001", desk_owner=player.playerId)
        desk.save()
    # player = PlayerModel.objects.all().first()
    # game = GameModel.objects.all().first()
    # try:
    #     pdg = PlayerDeskGame(desk="f5a7867e48b44cb1908bacb192214368", player=player, game=game, player_bet=20, player_win=30, player_remind=1000)
    #     pdg.save()
    # except Exception as e:
    #     print e
    #
    # bet = {"bank":100, "player":100,"tie":100, "bankPair":0, "playerPair":0}
    # bet_a = BetModel(**bet)
    # bet_a.save()
    # game = GameModel(desk="1001", all_bet=5000, all_paid=1200, game_result=[0, 3], player_cards=[7,8], bank_cards=[5,6])
    # game.save()
    # handle = HandSelModel(sender="888888", receiver="100003", points=1000, success=False)
    # handle.save()
    # desk = DeskModel(desk_id="1234567890")
    # desk.save()
    # game = GameModel(game_result=[1,2], bank_cards=[1,2,3], player_cards=[1,2,3,4])
    # game.save()
    # pdg = PlayerDeskGame(desk="1002", player=player, game=game, player_win=1200, player_bet=bet_a, player_remind=2000, is_banker=True)
    # pdg.save()
    # pdg1 = PlayerDeskGame.objects.filter(desk=desk)
    # print pdg1


