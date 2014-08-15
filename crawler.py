# -*- coding: utf-8 -*-

# Copyleft 2014 Paulo Luan <https://github.com/transparenciasjc>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import urllib2
import csv
import os

import time
import sys

from threading import Thread

from bs4 import BeautifulSoup

base_url = 'http://cnes.datasus.gov.br/'
state_json = {}

# Parsear todos os estados pegando os ids
def get_base_url():
    # http://cnes.datasus.gov.br/Lista_Tot_Es_Estado.asp
    states_url = base_url + 'Lista_Tot_Es_Estado.asp'
    return states_url


def get_state_url(state_id, state_name):
    # http://cnes.datasus.gov.br/Lista_Tot_Es_Municipio.asp?Estado=35&NomeEstado=SAO%20PAULO
    state_url = base_url + 'Lista_Tot_Es_Municipio.asp'
    param_state_id = 'Estado=35'
    param_state_name = 'NomeEstado=SAO%20PAULO'
    state_url += '?' + param_state_id + '&' + param_state_name


def get_city_url(state_id, state_name, city_code):
    # http://cnes.datasus.gov.br/Lista_Es_Municipio.asp?VEstado=35&VCodMunicipio=354990&NomeEstado=SAO%20PAULO
    city_url = base_url + 'Lista_Es_Municipio.asp'
    param_v_state = 'VEstado=' + state_id  # 35
    param_v_city_code = 'VCodMunicipio=' + city_code  # 354990
    city_url += '?' + param_v_state + '&' + param_v_city_code + '&' + param_state_name


def get_entity_url(state_id, unity_code, city_code):
    # http://cnes.datasus.gov.br/Exibe_Ficha_Estabelecimento.asp?VCo_Unidade=3549906891136&VEstado=35&VCodMunicipio=354990
    entity_url = 'Exibe_Ficha_Estabelecimento.asp'
    param_unity_code = 'VCo_Unidade=' + unity_code  # 3549906891136
    param_state = 'VEstado=' + state_id
    param_city = 'VCodMunicipio=' + city_code  # 354990
    entity_url += '?' + param_unity_code + '&' + param_state + '&' + param_city


def get_plain_html(url):
    # #print('Making a request: ', url)
    html = None 

    try:
        response = urllib2.urlopen(url, timeout=6000)
        html = response.read()
    except:
        pass

    return html


def get_offline_html(path):
    from bs4 import BeautifulSoup

    html = open(path)
    plain_html = html.read()
    tree = BeautifulSoup(plain_html)
    return tree


def get_states():
    states = []
    html = get_plain_html(get_base_url())
    tree = BeautifulSoup(html)

    div = tree.find('div',
                    {'style': 'width:300; height:209; POSITION: absolute; TOP: 185px; LEFT: 400px; overflow:auto'})
    table = div.find('table')

    for row in table.find_all('tr'):
        cols = row.find_all('td')

        state_json = {}
        state_json['estado_nome'] = cols[0].text
        state_json['estado_total'] = cols[1].text
        state_json['estado_%'] = cols[2].text
        state_json['url'] = base_url + cols[0].find('a')['href']

        states.append(state_json)  # TODO: append the entire url
    return states


def get_cities(state_url):
    cities = []
    html = get_plain_html(state_url)
    tree = BeautifulSoup(html)

    div = tree.find('div',
                    {'style': 'width:450; height:300; POSITION: absolute; TOP: 201px; LEFT: 180px; overflow:auto'})
    table = div.find('table')

    for row in table.find_all('tr'):
        cols = row.find_all('td')
        city_json = {}
        city_json['cidade_IBGE'] = cols[0].text
        city_json['cidade_nome'] = cols[1].text
        city_json['cidade_cadastrados'] = cols[2].text
        city_json['url'] = base_url + cols[1].find('a')['href']
        cities.append(city_json)

    return cities


def get_entities(city_url):
    entities = []
    html = get_plain_html(city_url)
    tree = BeautifulSoup(html)
    table = tree.find('table')  # there is only one table on the state's page
    links = table.findAll('a')
    for link in links:
        entities.append(base_url + link['href'])
    return entities


def parse_entity_data(entity_url):
    html = get_plain_html(entity_url)
    tree = BeautifulSoup(html)
    table = tree.find('table', attrs={
        'bgcolor': 'white'})  # the table that has the properties is the only that the bg is 'white'
    rows = []
    json = {}
    try:
        for row in table.find_all('tr'):
            rows.append([val.text.encode('utf8') for val in row.find_all('td')])
        json = list_to_json(rows)
    except:
        pass

    return json


def list_to_json(rows):
    json = {}
    j = 0
    # TODO: e se for par? vai ficar dado faltando?
    for i in range(len(rows)):
        try:
            temp_dict = dict(zip(rows[j], rows[j + 1]))
            json.update(temp_dict)  # append properties to json
            j += 2  # move to the next pair
        except:
            break
    return json


# TODO: mudar
def save_csv(json):
    file_name = 'output/' + json['estado_nome'].strip('\n') + '.csv'
    csvfile = open(file_name, 'a')
    writer = csv.writer(csvfile, delimiter=',')

    if (file_is_empty(file_name)):
        # ##print("\n\n")
        ###print("Keys: ", json.keys())
        writer.writerow(json.keys())

    # ##print("\n\n")
    ###print("values: ", json.values())
    writer.writerow(json.values())


def file_is_empty(path):    
    return os.stat(path).st_size == 0


def show_progress_message(message):
    #sys.stdout.write(message)
    os.system('clear')
    sys.stdout.write('\r%s' % message)
    sys.stdout.flush()


def merge_json(json1, json2):
    merged_json = {key: value for (key, value) in (json1.items() + json2.items())}
    if ('url' in merged_json): del merged_json['url']
    return merged_json


def get_cities_by_state(state):
    try:
        cities = get_cities(state['url'])
        #print('Cities: ', len(cities))        
    except Exception, e:
        pass

    return cities


def get_entities_by_city(city):
    entities = None
    try:
        entities = get_entities(city['url'])
        #print('Entities: ', len(entities))            
    except Exception, e:
        pass

    return entities

def merge_entity_with_cities(state, city, entity):
    try:
        base_json = merge_json(state, city)

        entity_json = parse_entity_data(entity)
        json = merge_json(base_json, entity_json)

        save_csv(json)

    except Exception, e:
        pass


def download_sp():
    states = get_states()   
    state = states[24] #sp
    cities = get_cities_by_state(state)

    for city_index, city in enumerate(cities):
        entities = get_entities_by_city(city)
    
        for entity_index, entity in enumerate(entities):
            show_progress_message('baixando entidade... ' + str(entity_index) + ' de ' + str(len(entities)) + "\nCidades: " + str(city_index) + " de " + str(len(cities)) + "\n Entidades: " + str(entity_index) + " de " + str(len(entities)) )
            th = Thread( target=merge_entity_with_cities, args = ( state, city, entity ) )
            th.start()
            #merge_entity_with_cities(state, city, entity)

def download_all_states():
    states = get_states()   
    #print('States: ', len(states))

    for state_index, state in enumerate(states):
        cities = get_cities_by_state(state)

        for city_index, city in enumerate(cities):
            entities = get_entities_by_city(city)

            for entity_index, entity in enumerate(entities):
                show_progress_message('baixando entidade... ' + str(entity_index) + ' de ' + str(len(entities)) + "Estados: "+ str(state_index) + " de " + str(len(states)) + "\nCidades: " + str(city_index) + " de " + str(len(cities)) + "\n Entidades: " + str(entity_index) + " de " + str(len(entities)) )
                merge_entity_with_cities(state, city, entity)
                ##print "Estados: ", state_index ," de ", len(states) , "\nCidades: " , city_index , " de " , len(cities) , "\n Entidades: " , entity_index , " de " , len(entities))

                


#initialize();
