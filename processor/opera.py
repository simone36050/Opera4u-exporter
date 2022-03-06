from math import fabs
from requests import Session
from datetime import date as Date, datetime as Datetime
from bs4 import BeautifulSoup, Tag, ResultSet

import traceback

DATE_ITALIAN_FORMAT = '%d/%m/%Y'

def new_session() -> Session:
    return Session()

def login(s: Session, username: str, password: str) -> bool:
    r = s.post('https://opera4u.operaunitn.cloud/area-riservata/login',
               allow_redirects=False,
               data={ 'coming_from': '',
                      'username': username,
                      'password': password })
    # 302: ok
    # 200: error
    return r.status_code == 302

def logout(s: Session):
    s.get('https://opera4u.operaunitn.cloud/area_riservata/logout')

def list_reservations_cateen(s: Session, cateen: int) -> dict:
    # request
    r = s.get('https://opera4u.operaunitn.cloud/prenota_tavolo/0/{}'.format(cateen))

    # not working
    if r.status_code != 200:
        return []

    # parse result
    try:
        reservations = []
        parser = BeautifulSoup(r.text, 'html.parser')

        table: Tag = parser.find('table', {'class': 'table table-striped'})
        tbody: Tag = table.find('tbody')

        # reservations
        trs: ResultSet = tbody.find_all('tr')
        for tr in trs:
            res = {}

            tr: Tag
            tds: Tag = tr.find_all('td')
            
            # description
            desc: Tag = tds[0]
            desc_info = [r.extract().string.strip() for r in desc.contents][0:2]

            # date
            res['date'] = Datetime.strptime(desc_info[0], DATE_ITALIAN_FORMAT).date()

            # time
            times = desc_info[1].split('(')[1].split(')')[0].split(' - ')
            res['time_from'] = Datetime.strptime(times[0], '%H:%M').time()
            res['time_to'] = Datetime.strptime(times[1], '%H:%M').time()

            # id
            delete: Tag = tds[1].find('button')
            res['id'] = int(delete.attrs['data-prenotazione'])

            reservations.append(res)

        return reservations
    except:
        return []
    

def list_reservations(s: Session) -> dict:
    cateends = {
        1: 'T. Gar',
        3: 'Mesiano',
        4: 'Povo 0',
        5: 'Povo 1'
    }

    reservations = []

    for cateen in cateends:
        res = list_reservations_cateen(s, cateen)
        for r in res:
            r['cateen'] = cateends[cateen]
        reservations.extend(res)

    from pprint import pprint
    pprint(reservations)
    return reservations
