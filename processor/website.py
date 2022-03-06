from flask import Flask, request, abort, Response, send_file, url_for
from datetime import date as Date, timedelta as Timedelta, datetime as Datetime
from icalendar import Calendar, Event
from uuid import uuid4
from os.path import exists
from barcode.writer import ImageWriter
from PIL.Image import Image
from io import BytesIO

import opera
import json
import barcode
import pytz

app = Flask(__name__)


# settings

DAYS = 7

DESCRIPTION = \
'''Mensa {}
Il {} dalle {} alle {}

{}

<a href="{}">Codice a barre</a>'''


# utils

def get_reservations(username: str, password: str) -> dict:
    s = opera.new_session()
    if not opera.login(s, username, password):
        return None

    reservations = opera.list_reservations(s)

    opera.logout(s)
    return reservations

def build_menu(date: Date) -> str:
    filename = '../data/menu/{}.json'.format(date.strftime('%Y-%W'))
    day_of_week = date.weekday()

    # check exist
    if not exists(filename):
        return None

    # build
    try:
        output = ''

        with open(filename) as f:
            menu = json.load(f)

        day_menu = menu[day_of_week]
        
        # dishes
        dishes = {
            'first': 'Primi',
            'second': 'Secondi',
            'side': 'Contorni'
        }

        for dish in dishes:
            output += '{}:<br><ul>'.format(dishes[dish])
            for item in day_menu[dish]:
                name = item['name']
                if item['in_reduced']:
                    name = '<b>{}</b>'.format(name)
                output += '<li>{}</li>'.format(name)
            output += '</ul>'

        return output
    except:
        return None


def build_ics(events: dict) -> str:
    cal = Calendar()
    cal['summary'] = 'Your Opera4u\' reservations'

    timezone = pytz.timezone('Europe/Rome')
    for event in events:
        ev = Event()
        ev['summary'] = 'Mensa'
        start = Datetime.combine(event['date'], event['time_from'])
        ev.add('dtstart', timezone.localize(start))
        ev.add('dtend', timezone.localize(start + Timedelta(hours=1)))
        ev['uid'] = '{}@tn_mensa.apps.simone36050.it'.format(uuid4())
        menu = build_menu(event['date'])
        ev['description'] = DESCRIPTION.format(
            event['cateen'],
            event['date'].strftime('%d/%m/%Y'),
            event['time_from'].strftime('%H:%M'),
            event['time_to'].strftime('%H:%M'),
            menu if menu != None else 'Menù non disponibile',
            'https://apps.simone36050.it/mensa/processor/render/{}'.format(event['id'])
        )
        cal.add_component(ev)

    return cal.to_ical()
    

# views

@app.route('/events')
def events():
    # check if the user know that password is store in cleartext
    if not request.args.get('i_known_that_password_is_stored_in_clear', default=False, type=bool):
        abort(400)

    username = request.args.get('username', default=None, type=str)
    password = request.args.get('password', default=None, type=str)
    
    if username == None or password == None:
        abort(400)

    events = get_reservations(username, password)
    ical = build_ics(events)

    res = Response(ical)
    res.headers["Content-type"] = "text/plain; charset=utf-8"
    return res

@app.route('/render/<int:id>')
def render(id: int):
    opera_id = 'PP-{}'.format(id)
    code: barcode.Code128 = barcode.get('code128', opera_id, writer=ImageWriter())
    img: Image = code.render()
    
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')


# debug

if __name__ == '__main__':
    app.run(debug=True)

