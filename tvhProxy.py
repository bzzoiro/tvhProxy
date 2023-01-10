from gevent import monkey; monkey.patch_all()

import time
import os
import requests
from gevent.pywsgi import WSGIServer
from requests.auth import HTTPBasicAuth


from flask import Flask, Response, request, jsonify, abort, render_template

app = Flask(__name__)

# URL format: <protocol>://<username>:<password>@<hostname>:<port>, example: https://test:1234@localhost:9981
config = {
    'username': 'admin',
    'password': 'admin',
    'port': 9981,
    'domain': '192.168.1.156', #'bzzoiro.duckdns.org',
    'bindAddr': os.environ.get('TVH_BINDADDR') or '',
    'tvhURL': os.environ.get('TVH_URL') or 'http://admin:admin@bzzoiro.duckdns.org:9981',
    'tvhProxyURL': os.environ.get('TVH_PROXY_URL') or 'http://bzzoiro.duckdns.org',
    'tunerCount': os.environ.get('TVH_TUNER_COUNT') or 1,  # number of tuners in tvh
    'tvhWeight': os.environ.get('TVH_WEIGHT') or 300,  # subscription priority
    'chunkSize': os.environ.get('TVH_CHUNK_SIZE') or 1024*1024,  # usually you don't need to edit this
    'streamProfile': os.environ.get('TVH_PROFILE') or 'pass'  # specifiy a stream profile that you want to use for adhoc transcoding in tvh, e.g. mp4
}

discoverData = {
    'FriendlyName': 'tvhProxy',
    'Manufacturer' : 'Silicondust',
    'ModelNumber': 'HDTC-2US',
    'FirmwareName': 'hdhomeruntc_atsc',
    'TunerCount': int(config['tunerCount']),
    'FirmwareVersion': '20150826',
    'DeviceID': '12345678',
    'DeviceAuth': 'test1234',
    'BaseURL': '%s' % config['tvhProxyURL'],
    'LineupURL': '%s/lineup.json' % config['tvhProxyURL']
}


def compose_root_url():
    return 'http://{}:{}@{}:{}'.format(config['username'], config['password'], config['domain'], config['port'])

@app.route('/discover.json')
def discover():
    return jsonify(discoverData)


@app.route('/lineup_status.json')
def status():
    return jsonify({
        'ScanInProgress': 0,
        'ScanPossible': 1,
        'Source': "Cable",
        'SourceList': ['Cable']
    })


@app.route('/lineup.json')
def lineup():
    lineup = []

    for c in _get_channels():
        if c['enabled']:

            url = '{}/stream/channel/{}'.format(compose_root_url(), c['uuid'])

            lineup.append({'GuideNumber': str(c['number']),
                           'GuideName': c['name'],
                           'URL': url
                           })

    return jsonify(lineup)


@app.route('/lineup.post', methods=['GET', 'POST'])
def lineup_post():
    return ''

@app.route('/')
@app.route('/device.xml')
def device():
    return render_template('device.xml',data = discoverData),{'Content-Type': 'application/xml'}


def _get_channels():

    ts_url = 'api/channel/grid?start=0&limit=999999'
    url = '%s/%s' % (compose_root_url(),ts_url,)
    print(url)
    r = requests.get(url)

    return r.json()['entries']



if __name__ == '__main__':
    print('----------------------------------------------------------------------------')
    http = WSGIServer((config['bindAddr'], 5004), app.wsgi_app)
    http.serve_forever()
