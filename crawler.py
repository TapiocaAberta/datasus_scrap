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
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import urllib2
import csv
import os

import time
import sys

from bs4 import BeautifulSoup

base_url = "http://cnes.datasus.gov.br/"
state_json = {}

# Parsear todos os estados pegando os ids
def get_base_url():
    # http://cnes.datasus.gov.br/Lista_Tot_Es_Estado.asp
    states_url = base_url + "Lista_Tot_Es_Estado.asp"
    return states_url


def get_state_url(state_id, state_name):
    # http://cnes.datasus.gov.br/Lista_Tot_Es_Municipio.asp?Estado=35&NomeEstado=SAO%20PAULO
    state_url = base_url + "Lista_Tot_Es_Municipio.asp"
    param_state_id = "Estado=35"
    param_state_name = "NomeEstado=SAO%20PAULO"
    state_url += "?" + param_state_id + "&" + param_state_name


def get_city_url(state_id, state_name, city_code):
    # http://cnes.datasus.gov.br/Lista_Es_Municipio.asp?VEstado=35&VCodMunicipio=354990&NomeEstado=SAO%20PAULO
    city_url = base_url + "Lista_Es_Municipio.asp"
    param_v_state = "VEstado=" + state_id  # 35
    param_v_city_code = "VCodMunicipio=" + city_code  # 354990
    city_url += "?" + param_v_state + "&" + param_v_city_code + "&" + param_state_name


def get_entity_url(state_id, unity_code, city_code):
    # http://cnes.datasus.gov.br/Exibe_Ficha_Estabelecimento.asp?VCo_Unidade=3549906891136&VEstado=35&VCodMunicipio=354990
    entity_url = "Exibe_Ficha_Estabelecimento.asp"
    param_unity_code = "VCo_Unidade=" + unity_code  # 3549906891136
    param_state = "VEstado=" + state_id
    param_city = "VCodMunicipio=" + city_code  # 354990
    entity_url += "?" + param_unity_code + "&" + param_state + "&" + param_city


def get_plain_html(url):
    print("Making a request: ", url)
    response = urllib2.urlopen(url, timeout=6000)
    html = response.read()
    return html


def get_states():
    states = []
    html = get_plain_html(get_base_url())
    tree = BeautifulSoup(html)
    for state in tree('area'):
        states.append(base_url + state['href'])  #TODO: append the entire url
    return states


def get_cities(state_url):
    cities = []
    html = get_plain_html(state_url)
    tree = BeautifulSoup(html)
    table = tree.find('table')  # there is only one table on the state's page
    links = table.findAll('a')
    for link in links:
        cities.append(base_url + link['href'])  #TODO: append the entire url
    return cities


def get_entities(city_url):
    entities = []
    html = get_plain_html(city_url)
    tree = BeautifulSoup(html)
    table = tree.find('table')  # there is only one table on the state's page
    links = table.findAll('a')
    for link in links:
        entities.append(base_url + link['href'])  #TODO: append the entire url
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
    #TODO: e se for par? vai ficar dado faltando?
    for i in range(len(rows)):
        try:
            temp_dict = dict(zip(rows[j], rows[j + 1]))
            json.update(temp_dict)  # append properties to json
            j += 2  # move to the next pair
        except:
            break
    return json


#TODO: mudar
def save_csv(json):
    csvfile = open('output.csv', 'a')
    writer = csv.writer(csvfile, delimiter=',')

    if (file_is_empty('output.csv')):
        writer.writerow(json.keys())

    writer.writerow(json.values())


def file_is_empty(path):
    return os.stat(path).st_size == 0


def increase_progress_bar(progress):
    sys.stdout.write("\r%d%%" % progress)
    sys.stdout.flush()


def initialize():
    states = get_states()
    print("get states: ", len(states))

    for state in states:
        cities = get_cities(state)
        print("get cities: ", len(cities))

        for city in cities:
            entities = get_entities(city)
            print("get entities: ", len(entities))

            for entity in entities:
                json = parse_entity_data(entity)
                print(json)
                save_csv(json)


initialize();
