from flask import request, session
from flask_socketio import leave_room, emit, join_room

import errors
from app import socketio
from game_manager import shared as game_manager


@socketio.on('disconnect', namespace='/game')
def on_disconnect():
    player_id = session.get('player_id')
    game_id = session.get('game_id')
    if player_id is not None:
        player = game_manager.request_player(player_id)
        game_manager.deactivate_player(player)


@socketio.on('update_session', namespace='/game')
def on_update_session(info):
    old_sid = info.get('sid', None)
    game_id = info['game_id']
    if old_sid is not None:
        try:
            player = game_manager.request_player_with_sid(old_sid, game_id)
            game_manager.update_player_sid(old_sid, request.sid)
            game_manager.activate_player(player)
            game = player.game
            join_room(player.game.host_id)
            emit('game_updated', game.to_dict(), room=game.host_id, broadcast=False, namespace='/game')
        except errors.UknownPlayer:
            return {'sid': request.sid}
        except errors.GameError as err:
            return str(err)
    return {'sid': request.sid}


@socketio.on('leave_game', namespace='/game')
def on_leave(info):
    game_id = info['game_id']
    player_id = info['player_id']
    try:

        player = game_manager.request_player(player_id)
        game_manager.leave_game(game_id, request.sid, player_id)
        game = game_manager.request_game(game_id)
        emit('game_updated', game.to_dict(), room=game.host_id, broadcast=True, namespace='/game')
        emit('game_list', [game.to_dict(False) for game in game_manager.request_games()],
             namespace='/lobby', broadcast=True)
        del session['player_id']
        leave_room(game.host_id, sid=player.sid)
        return 'You left game'
    except errors.GameError as err:
        return str(err)


@socketio.on('start_game', namespace='/game')
def on_start(info):
    game_id = info['game_id']
    try:
        game = game_manager.request_game(game_id)
        game_manager.update_game(game, sid=request.sid).execute()
        return 'Game started'
    except errors.GameError as err:
        return str(err)


@socketio.on('restart_game', namespace='/game')
def on_restart(info):
    game_id = info['game_id']
    try:
        game = game_manager.request_game(game_id)
        game = game_manager.new_game(game, sid=request.sid)
        game_manager.update_game(game, sid=request.sid).execute()
        return 'Game restarted'
    except errors.GameError as err:
        return str(err)


@socketio.on('delete_game', namespace='/game')
def on_delete_game(info):
    game_id = info['game_id']
    try:
        game = game_manager.request_game(game_id)
        game_manager.try_delete_game(game_id, request.sid)
        emit('game_updated', 'Game deleted', room=game.host_id)
        emit('game_list', [game.to_dict(False) for game in game_manager.request_games()],
             namespace='/lobby', broadcast=True)
        del session['player_id']
        return 'Game deleted'
    except errors.GameError as err:
        return str(err)


@socketio.on('make_proposal', namespace='/game')
def on_proposal(info):
    game_id = info['game_id']
    players_ids = info['players_id']
    try:
        game = game_manager.request_game(game_id)
        game_manager.update_game(game, players_ids=players_ids, sid=request.sid).execute()
        return 'Proposal made'
    except errors.GameError as err:
        return str(err)


@socketio.on('vote', namespace='/game')
def on_vote(info):
    result = info['result']
    game_id = info['game_id']
    try:
        game = game_manager.request_game(game_id)
        game_manager.update_game(game, result=result, sid=request.sid).execute()
        return 'Vote made'
    except errors.GameError as err:
        return str(err)


@socketio.on('join_game', namespace='/game')
def on_join(info):
    game_id = info['game_id']
    username = info['username']
    try:
        game = game_manager.request_game(game_id)
        player = game_manager.join_game(game, username, request.sid)
        game = game_manager.request_game(game_id)
        join_room(game.host_id, namespace='/game')
        session['player_id'] = player.id
        emit('game_updated', game.to_dict(), room=game.host_id, broadcast=True, namespace='/game')
        return {'game': game.to_dict(), 'player': player.to_dict(), 'sid': request.sid}
    except errors.GameError as err:
        return str(err)


@socketio.on('create_game', namespace='/game')
def on_create_game(info):
    username = info['username']
    try:
        game = game_manager.create_game(username, request.sid)
        join_room(game.host_id, namespace='/game')
        emit('game_list', [game.to_dict(False) for game in game_manager.request_games()],
             broadcast=True, namespace='/lobby')
        session['player_id'] = game.host_id
        return {'game': game.to_dict(), 'player': game.host.to_dict(), 'sid': request.sid}
    except errors.GameError as err:
        return str(err)
