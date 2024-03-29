from unittest import TestCase
from app import create_app, db, socketio
import numpy as np
from unittest import TestCase

import numpy as np

np.random.seed(13)


class TestGameSetupStart(TestCase):

    def setUp(self):
        self.app = create_app('config.Test')

    def tearDown(self):
        with self.app.app_context():
            db.drop_all()

    def test_reconnect_make_proposal_success(self):
        client1 = socketio.test_client(self.app, flask_test_client=self.app.test_client())
        client1.connect('/game')
        client2 = socketio.test_client(self.app, flask_test_client=self.app.test_client())
        client2.connect('/game')
        client3 = socketio.test_client(self.app, flask_test_client=self.app.test_client())
        client3.connect('/game')
        client4 = socketio.test_client(self.app, flask_test_client=self.app.test_client())
        client4.connect('/game')
        client5 = socketio.test_client(self.app, flask_test_client=self.app.test_client())
        client5.connect('/game')

        result1 = client1.emit('create_game', {'username': 'Ivan'}, namespace='/game', callback=True)
        result2 = client2.emit('join_game', {'username': 'Petr', 'game_id': result1['game']['id']},
                               namespace='/game', callback=True)
        result3 = client3.emit('join_game', {'username': 'Liza', 'game_id': result1['game']['id']},
                               namespace='/game', callback=True)
        result4 = client4.emit('join_game', {'username': 'Dima', 'game_id': result1['game']['id']},
                               namespace='/game', callback=True)
        result5 = client5.emit('join_game', {'username': 'Kosta', 'game_id': result1['game']['id']},
                               namespace='/game', callback=True)
        print(client1.get_received())
        self.assertTrue(client1.emit('start_game', {'game_id': result1['game']['id']},
                       namespace='/game', callback=True) == 'Game started')
        game1 = client1.get_received(namespace='/game')[-1]['args'][0]
        old_leader = game1['details']['leader_id']
        client1.emit('update_session', {'sid': result1['sid'], 'game_id': result1['game']['id']}, namespace='/game')
        game2 = client1.get_received(namespace='/game')[-1]['args'][0]
        self.assertTrue(game2['details']['leader_id'] == old_leader)
