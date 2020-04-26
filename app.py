from flask import Flask, abort, redirect, url_for, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
from math import trunc
import uuid
import health


class Topic:
    def __init__(self, name, description, sound, last_read):
        self.id = str(uuid.uuid4())
        self.liveness_threshold = 30 * 60
        self.name = name
        self.description = description
        self.sound = sound
        self.last_read = last_read
        self.events = [0] * event_memory # timestamps of previous events
        self.check()

    def check(self):
        return True

    def is_active(self):
        return current_epoch_time() - self.last_read > self.liveness_threshold

    def client_dto(self, full=False):
        dto = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'sound': self.sound
        }
        if full:
            dto['events'] = [t for t in self.events]
        return dto

def load_dummy_data():
    global topics
    time = trunc(datetime.utcnow().timestamp())
    for topic in [
        Topic(
            'Arthur',
            "For when you realize that everyday when you're walking down the street, everybody that you meet has an original point of view",
            'https://www.myinstants.com/media/sounds/bazinga.swf.mp3',
            time
        ),
        Topic(
            'George!',
            'You knew this was coming....',
            'https://www.myinstants.com/media/sounds/joke_drum_effect.mp3',
            time
        ),
        Topic(
            'Dexter',
            'No, not Dexter Gordon.',
            'https://www.myinstants.com/media/sounds/surprise-motherfucker.mp3',
            time
        )]:
        topics[topic.id] = topic

topic_limit = 256
event_memory = 5 # remember and return up to only the last 5 events in a topic

app = Flask(__name__)
CORS(app)
topics = {} # topic.id: topic
load_dummy_data()


def current_epoch_time():
    return trunc(datetime.utcnow().timestamp())

def evict_topics():
    global topics
    before = len(topics)
    topics = {id: topic for id, topic in topics.items() if topic.is_active()}
    after = len(topics)
    removed = before - after
    app.logger.info('evicted {} topics'.format(after))
    return removed

@app.route('/')
def home():
    return redirect(url_for('list_topics'))

@app.route('/topics/')
def list_topics():
    app.logger.info('listing topics...')
    return jsonify(status='ok',
                   time=current_epoch_time(),
                   topics=[t.client_dto() for t in topics.values()])

@app.route('/topics/', methods=['POST'])
def add_topic():
    """
    TODO: implement this method
    """
    # return ''
    payload = request.get_json(silent=True)
    if payload is None:
        return abort(400)
    time = current_epoch_time()
    new_topic = Topic(payload.get('name'),
                      payload.get('description'),
                      payload.get('sound'),
                      time)
    if len(topics) >= topic_limit:
        if evict_topics() == 0:
            raise Exception('too many active topics; could not register new topic')
    topics[new_topic.id] = new_topic
    return jsonify(status='ok',
                   time=time,
                   topic=new_topic.client_dto())

@app.route('/topics/<id>', methods=['PUT'])
def record_event(id):
    if id not in topics:
        abort(404)
    topic = topics[id]
    time = current_epoch_time()
    topic.events.append(time)
    topic.events.pop(0)
    return jsonify(status='ok',
                   time=time)

@app.route('/topics/<id>')
def read_topic(id):
    if id not in topics:
        abort(404)
    topic = topics[id]
    after_time = int(request.args.get('after')) if 'after' in request.args else 0
    dto = topic.client_dto(full=True)
    dto['events'] = [t for t in dto['events'][:event_memory] if t > after_time]
    return jsonify(status='ok',
                   time=current_epoch_time(),
                   topic=dto)

@app.route('/health')
def health_check():
    return health.check()
