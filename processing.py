# %%
import json
import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
opt = webdriver.ChromeOptions()
opt.add_argument('--headless')
opt.add_argument('--no-sandbox')
opt.add_argument('--disable-dev-shm-usage')

# %%
matriculas = pd.read_csv('matriculas.csv', sep=';', index_col='RBD')[['MAT_TOTAL', 'COD_DEPE2']]
matriculas.index = matriculas.index.astype(str)

IVE_FILE_PATH = 'IVE.xlsx'

ive_file_basica = pd.read_excel(IVE_FILE_PATH, sheet_name='BASICA', header=4, index_col='ID_RBD')[['DS_REGION_ESTABLE', 'IVE-SINAE BÁSICA 2023', 'DS_RURALIDAD']]
ive_file_basica = ive_file_basica[ive_file_basica.index.notnull()]
ive_file_basica.index = ive_file_basica.index.astype(int).astype(str)

ive_file_media = pd.read_excel(IVE_FILE_PATH, sheet_name='MEDIA', header=4, index_col='ID_RBD')[['DS_REGION_ESTABLE', 'IVE-SINAE MEDIA 2023', 'DS_RURALIDAD']]
ive_file_media = ive_file_media[ive_file_media.index.notnull()]
ive_file_media.index = ive_file_media.index.astype(int).astype(str)

# %%
indicator_mapping = {
    4: {
        'singleValue': {
            'indicador-1-2': 'Autoestima académica y motivación escolar',
            'indicador-2-2': 'Clima de convivencia escolar',
            'indicador-3-2': 'Participación y formación ciudadana',
            'indicador-4-2': 'Hábitos de vida saludables',
            'indicador-5-2': 'Simce Lenguaje',
            'indicador-8-2': 'Simce Matemática',
        },
        'simceLevel': {
            'indicador-6': ['Len Nivel Insuficiente', 'Len Nivel Elemental', 'Len Nivel Adecuado'],
            'indicador-9': ['Mat Nivel Insuficiente', 'Mat Nivel Elemental', 'Mat Nivel Adecuado']
        }
    },
    2: {
        'singleValue': {
            'indicador-11-2': 'Autoestima académica y motivación escolar',
            'indicador-12-2': 'Clima de convivencia escolar',
            'indicador-13-2': 'Participación y formación ciudadana',
            'indicador-14-2': 'Hábitos de vida saludables',
            'indicador-15-2': 'Simce Lenguaje',
            'indicador-18-2': 'Simce Matemática',
        },
        'simceLevel': {
            'indicador-16': ['Len Nivel Insuficiente', 'Len Nivel Elemental', 'Len Nivel Adecuado'],
            'indicador-19': ['Mat Nivel Insuficiente', 'Mat Nivel Elemental', 'Mat Nivel Adecuado']
        }
    }
}
missing_ind = {
    'indicador-16': 'Lengua y Literatura: Lectura',
    'indicador-19': 'Matemática',
    'indicador-6': 'Lenguaje y Comunicación: Lectura',
    'indicador-9': 'Matemática'
}
# Las dimensiones a veces generan gráficos, y otras generan tablas, el proximo año manejar ese caso en el scraper
# lo mismo con algunos indicadores

dimension_mapping = {
    2: {
        'dimension-38': 'Autopercepción y autovaloración académica',
        'dimension-39': 'Motivación escolar',
        'dimension-40': 'Ambiente de respeto',
        'dimension-41': 'Ambiente organizado',
        'dimension-42': 'Ambiente seguro',
        'dimension-43': 'Sentido de pertenencia',
        'dimension-44': 'Participación',
        'dimension-45': 'Vida democrática',
        'dimension-46': 'Hábitos de autocuidado',
        'dimension-47': 'Hábitos alimenticios',
        'dimension-48': 'Hábitos de vida activa'
    },
    4: {
        'dimension-21': 'Autopercepción y autovaloración académica',
        'dimension-22': 'Motivación escolar',
        'dimension-23': 'Ambiente de respeto',
        'dimension-24': 'Ambiente organizado',
        'dimension-25': 'Ambiente seguro',
        'dimension-26': 'Sentido de pertenencia',
        'dimension-27': 'Participación',
        'dimension-28': 'Vida democrática',
        'dimension-29': 'Hábitos de autocuidado',
        'dimension-30': 'Hábitos alimenticios',
        'dimension-31': 'Hábitos de vida activa'
    }
}

cod_depe2_mapping = {
    1: 'Municipal',
    2: 'Part. subvencionado',
    3: 'Particular pagado',
    4: 'Corp de administración delegada',
    5: 'Servicio local de educación'
}

request_credentials = {
    "username": 'profesor',
    "password": 'profe2020',
    "profile": 'docente'
}

# %%
def authUrl(rbd):
    queryParams = 'auth?client_id=agencia&response_type=code&state=1'
    redirect = f'redirect_uri=http://www.simce.cl/validation/{rbd}'
    baseUrl = 'https://perfilador.agenciaeducacion.cl/auth/realms/Perfilador/protocol/openid-connect/'
    return f'{baseUrl}{queryParams}&{redirect}'

def get_gse(rbd, level):
    s = requests.Session()
    res = s.get(authUrl(rbd))
    log_url = BeautifulSoup(res.content, features="lxml").find('form')['action']
    s.post(log_url, data=request_credentials)
    page = BeautifulSoup(s.get(f'https://www.simce.cl/{rbd}/indicador').content, 'html.parser').find('section', id=level)
    div = [x for x in page.find_all('h5', {"class": 'level-title mb-3'}) if 'GSE' in x.get_text()][0]
    match = re.search(r'GSE:\s*(\w+(?:\s+\w+)?)', div.get_text().split('\n')[0])
    return match.group(1)

def get_dimensions_page(rbd):
    driver = webdriver.Chrome(options=opt)
    driver.get(authUrl(rbd))
    try:
        teacher_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "btnDocente"))
        )
        teacher_button.click()
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Seguir a resultados educativos')]"))
        )
        driver.get(f'https://www.simce.cl/{rbd}/dimension')
        page = driver.page_source
        driver.quit()
        return BeautifulSoup(page)
    except:
        driver.quit()

def get_indicators_page(rbd):
    driver = webdriver.Chrome(options=opt)
    driver.get(authUrl(rbd))
    try:
        teacher_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "btnDocente"))
        )
        teacher_button.click()
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Seguir a resultados educativos')]"))
        )
        driver.get(f'https://www.simce.cl/{rbd}/indicador')
        page = driver.page_source
        driver.quit()
        return BeautifulSoup(page)
    except:
        driver.quit()

def add_dimensions(school_data, dimensions, level):
    data = {}
    rbd = school_data['rbd']
    school_data = school_data['dimensiones']
    for k, v in school_data.items():
        if k in dimensions.keys():
            idx = v['coordsX'].index('2023')
            data[dimensions[k]] = v['dataPoints'][idx]
    not_graph = [v for v in dimensions.values() if v not in data.keys()]
    if len(not_graph) > 0:
        try:
            page = get_dimensions_page(rbd).find('section', id=level).find_all('div', {'class': 'col-md-6 mb-4'})
            divs = list(filter(lambda x: 'Simbología' not in x.get_text() and x.find('h4', {'class': 'title-chart'}).get_text() in not_graph, page))
            for i in divs:
                data[i.find('h4').get_text()] = pd.read_html(str(i.find('table')))[0].iloc[0]['Promedio 2023']
        except Exception as e:
            print(e)
            with open(f'error/{rbd}.txt', 'w') as f:
                f.write(f'error dimensiones {level} {e}')
            return 'Error'
    return data


def add_indicators(school_data, indicators, level):
    data = {}
    rbd = school_data['rbd']
    school_data = school_data['indicadores']
    for k, v in school_data.items():
        if k in indicators['singleValue'].keys():
            key = indicators['singleValue'][k]
            data[key] = v['dataPoints'][-1]['data'][0]
        elif k in indicators['simceLevel'].keys():
            idx = v['coordsX'].index('2023')
            for i, value in enumerate(indicators['simceLevel'][k]):
                data[value] = v['dataPoints'][i]['data'][idx]
    # not_graph = [v for v in indicators['singleValue'].values() if v not in data.keys()]
    not_graph = [missing_ind[k] for k, v in indicators['simceLevel'].items() if v[0] not in data.keys()]
    if len(not_graph) > 0:
        try:
            page = get_indicators_page(rbd).find('section', id=level).find_all('div', {"class": 'row gx-5 mb-5'})
            divs = list(filter(lambda x: x.find('h5').get_text() in not_graph, page))
            for i in divs:
                table = (
                    [x for x in i.findAll('div', {'class': 'col-md-6 mb-4'}) if 'Distribución de estudiantes' in x.get_text()] \
                         or [x for x in i.findAll('div', {'class': 'col-md-6 mb-4 min-printed'}) if 'Distribución de estudiantes' in x.get_text()]
                )[0]
                df = pd.read_html(str(table.find('table')), index_col='Nivel')[0].loc[:,'Promedio 2023']
                if 'Lectura' in i.get_text():
                    for idx, row in df.items():
                        data[f'Len {idx}'] = row.strip('%')
                elif 'Matemática' in i.get_text():
                    for idx, row in df.items():
                        data[f'Mat {idx}'] = row.strip('%')
        except Exception as e:
            with open(f'error/{rbd}.txt', 'w') as f:
                print(e)
                f.write(f'error indicadores {level} {e}')
            return 'Error'
    return data

def cuarto_basico(school_data):
    if school_data['indicadores']['indicador-1-2']['dataPoints'][0]['data'] == [""]:
        return {}
    data = {}
    data['Nivel'] = '4 básico'
    rbd = school_data['rbd']
    if rbd in ive_file_basica.index:
        ive = ive_file_basica.loc[rbd]
        data['Region'] = ive['DS_REGION_ESTABLE']
        data['IVE'] = ive['IVE-SINAE BÁSICA 2023']
        data['Rural'] = ive['DS_RURALIDAD']
    if rbd in matriculas.index:
        matricula = matriculas.loc[rbd]
        data['MATRICULA_BASICA_MEDIA'] = matricula['MAT_TOTAL']
        data['Dependencia'] = cod_depe2_mapping[int(matricula['COD_DEPE2'])]
    data['GSE'] = get_gse(rbd, 'basic')
    indicators = add_indicators(school_data, indicator_mapping[4], 'basic')
    dimensions = add_dimensions(school_data, dimension_mapping[4], 'basic')
    if indicators == 'Error' or dimensions == 'Error':
        return 'Error'
    return {**data, **indicators, **dimensions}

def segundo_medio(school_data):
    if school_data['indicadores']['indicador-11-2']['dataPoints'][0]['data'] == [""]:
        return {}
    data = {}
    rbd = school_data['rbd']
    data['Nivel'] = 'II medio'
    if rbd in ive_file_media.index:
        ive = ive_file_media.loc[rbd]
        data['Region'] = ive['DS_REGION_ESTABLE']
        data['IVE'] = ive['IVE-SINAE MEDIA 2023']
        data['Rural'] = ive['DS_RURALIDAD']
    if rbd in matriculas.index:
        matricula = matriculas.loc[rbd]
        data['MATRICULA_BASICA_MEDIA'] = matricula['MAT_TOTAL']
        data['Dependencia'] = cod_depe2_mapping[int(matricula['COD_DEPE2'])]
    data['GSE'] = get_gse(rbd, 'medium')
    indicators = add_indicators(school_data, indicator_mapping[2], 'medium')
    dimensions = add_dimensions(school_data, dimension_mapping[2], 'medium')
    if indicators == 'Error' or dimensions == 'Error':
        return 'Error'
    return {**data, **indicators, **dimensions}

def process_school_data(file_name):
    file = open(file_name, 'r')
    school_data = json.load(file)
    file.close()
    data = []
    school_row = {
        'Año': [2023],
        'RBD': [school_data['rbd']],
        'Colegio': [school_data['nombre_colegio']],
        'Comuna': [school_data['comuna']],
    }
    basica = cuarto_basico(school_data)
    media = segundo_medio(school_data)
    if basica == 'Error' or media == 'Error':
        return []
    if basica:
        data.append(pd.DataFrame.from_dict({**school_row, **basica}))
    if media:
        data.append(pd.DataFrame.from_dict({**school_row, **media}))
    if len(data) == 0:
        return []
    return pd.concat(data)
import pickle
def process_schools(schools):
    data = []
    for i in schools:
        data.append(process_school_data(f'jsons/{i}'))
    data = [x for x in data if (isinstance(x, list) and x) or (isinstance(x, pd.DataFrame) and not x.empty)]
    if len(data) == 0:
        return
    df = pd.concat(data)
    df.to_pickle(f'./dfs3/{schools[0]}-{schools[-1]}')
from multiprocessing import Pool
n_workers = max(os.cpu_count() - 2, 2)
def main():
    files = os.listdir('jsons')
    ready = os.listdir('dfs')
    indexes_range = [[files.index(x.split('-')[0]), files.index(x.split('-')[1])] for x in ready]
    indexes = []
    for i in indexes_range:
        indexes.extend(list(range(i[0], i[1]+1, 1)))
    files2 = [v for i, v in enumerate(files) if i not in indexes]
    if files2 == []:
        files = os.listdir('error')
        files2 = [x.replace('.txt', '.json') for x in files]
    sub_schools_list = [files2[i: i+n_workers] for i in range(0, len(files2), n_workers)]
    with Pool(n_workers) as p:
        p.map(process_schools, sub_schools_list)


# %%
def fix_gse(df):
    try:
        print(f'starting chunk {df["RBD"].iloc[0]} - {df["RBD"].iloc[-1]}')
        df['GSE'] = df.apply(lambda x: get_gse(x['RBD'], ('basic' if x['Nivel'] == '4 básico' else 'medium')), axis=1)
        df.to_csv(f'./fix_gse/datos{df["RBD"].iloc[0]} - {df["RBD"].iloc[-1]}.csv', index=False)
    except:
        print(f'failed chunk {df["RBD"].iloc[0]} - {df["RBD"].iloc[-1]}')

def fix_gse_starter():
    df = pd.read_csv('datos2023.csv')
    import numpy as np
    arrays = np.array_split(df, 10)
    indexes = [int(x.strip('datos').split('-')[0]) for x in os.listdir('fix_gse')]
    new_arr = []
    for i in range(len(arrays)):
        if arrays[i]["RBD"].iloc[0] not in indexes:
            new_arr.append(arrays[i])
    fix_gse(new_arr[0])