#import libraries
from selenium import webdriver
import requests
import re
from bs4 import BeautifulSoup
import json
import os
from multiprocessing import Pool
import chromedriver_autoinstaller
chromedriver_autoinstaller.install()

#initialize constants

request_credentials = {
    "username": 'profesor',
    "password": 'profe2020',
    "profile": 'docente'
}

base_script = """
const dataP = {};
var dummy = "";

function getMaxValue(dataPoints) {
    if (Array.isArray(dataPoints[0].data)) {
        return Math.max(...dataPoints.map(dataset => Math.max(...dataset.data)));
    } else {
        return Math.max(...dataPoints);
    }
}

function designGraphics(idName, format, type, coordsX, dataPoints, stepSize, max, sigDif = null, dif = null, mDif =
        null) {
        const data = {
          format: format,
          coordsX: coordsX,
          dataPoints: dataPoints,
          sigDif: sigDif,
          dif: dif,
          mDif: mDif
        }

        dataP[idName] = data;
    }
"""

end_script = """
scrapFunction();

return dataP
"""

instructions_to_replace = [
    "document.getElementById('div-' + i + '-2').style.marginTop",
    "document.getElementById('dif-' + i + '-2').innerHTML",
    "container.innerHTML",
    "padreCanvas.innerHTML",
    "document.Fdocument('dif-' + i + '-2').innerHTML",
    "canvasContainer.parentNode"
  ]
replacement = "dummy"

pattern = r"\b(?:" + "|".join(map(re.escape, instructions_to_replace)) + r")\b"

opt = webdriver.ChromeOptions()
opt.add_argument('--headless')
opt.add_argument('--no-sandbox')
opt.add_argument('--disable-dev-shm-usage')
opt.add_argument("--remote-debugging-port=9222")

n_workers = max(os.cpu_count() - 2, 1)

def authUrl(rbd):
    queryParams = 'auth?client_id=agencia&response_type=code&state=1'
    redirect = f'redirect_uri=http://www.simce.cl/validation/{rbd}'
    baseUrl = 'https://perfilador.agenciaeducacion.cl/auth/realms/Perfilador/protocol/openid-connect/'
    return f'{baseUrl}{queryParams}&{redirect}'

def set_script(script):
  index = script.find("document.addEventListener('DOMContentLoaded', function()")
  script = script[index:]\
    .replace("document.addEventListener('DOMContentLoaded', function()", "function scrapFunction()")\
    .replace("});\n\n    window.onload", "};\n\n    window.onload")
  end_index = script.find("window.onload")
  script = re.sub(pattern, replacement, script[:end_index])
  return base_script + "\n\n" + script + "\n\n" + end_script

def scrap(rbd):
  s = requests.Session()
  res = s.get(authUrl(rbd))
  log_url = BeautifulSoup(res.content).find('form')['action']
  s.post(log_url, data=request_credentials)
  landing = BeautifulSoup(s.get(f'https://www.simce.cl/{rbd}/inicio').content, 'html.parser')
  if landing.find_all('script')[-1].text.find("(parseInt('2023')") == -1:
    return -1

  indicator_page = BeautifulSoup(s.get(f'https://www.simce.cl/{rbd}/indicador').content, 'html.parser')
  dimension_page = BeautifulSoup(s.get(f'https://www.simce.cl/{rbd}/dimension').content, 'html.parser')

  school_type = indicator_page.find(id='dependencia').text
  municipality = indicator_page.find(id='comuna').text
  gse = indicator_page.find_all(class_='level-title mb-3')
  gse = list(filter(lambda x: 'GSE' in x.text, gse))[0].find(id='selectedOption').text

  indicator_script = indicator_page.find_all('script')[-1].get_text()
  dimension_script = dimension_page.find_all('script')[-1].get_text()
  return {
    'indicator_script': indicator_script,
    'dimension_script': dimension_script,
    'school_type': school_type,
    'municipality': municipality,
    'GSE': gse
  }

def process_schools(schools):
  errors = []
  no_data = []
  # results = []
  driver = webdriver.Chrome(options=opt)
  for school in schools:
    try:
      scrap_data = scrap(str(school['rbd']))
      if scrap_data == -1:
        no_data.append(str(school['rbd']))
        continue
      indicators = driver.execute_script(set_script(scrap_data['indicator_script']))
      dimensions = driver.execute_script(set_script(scrap_data['dimension_script']))
      data = {
          'nombre_colegio': school['rbd_nombre'],
          'rbd': school['rbd'],
          'dependencia': scrap_data['school_type'],
          'comuna': scrap_data['municipality'],
          'GSE': scrap_data['GSE'],
          'indicadores': indicators,
          'dimensiones': dimensions,
      }
      with open(f"jsons/{data['rbd']}.json", "w", encoding='utf8') as output:
          json.dump(data, output, indent=2, ensure_ascii=False)
      # results.append(data)
    except Exception as e:
      print(f"error {e} on {school['rbd']}")
      errors.append([school['rbd'], e])
  driver.quit()
  return errors, no_data

def main():
  schools_file = open('establecimientos.json')
  schools = json.load(schools_file)
  schools_file.close()
  os.makedirs('jsons', exist_ok=True)
  errors = []
  no_data = []
  sub_schools_list = [schools[i*len(schools)//n_workers: (i+1)*len(schools)//n_workers] for i in range(n_workers)]
  with Pool(n_workers) as p:
    feedback = p.map(process_schools, sub_schools_list)
  errors, no_data = zip(*feedback)
  errors, no_data = [inner_list[0] for inner_list in errors if inner_list], [inner_list[0] for inner_list in no_data if inner_list]
  # results = np.array(results).flatten()
  # for i in results:
  #    with open(f"jsons/{i['rbd']}.json", "w", encoding='utf8') as output:
  #         json.dump(i, output, indent=2, ensure_ascii=False)
  if len(errors) > 0:
    with open(f"errores.txt", "w") as output:
          output.write('\n'.join(str(error) for error in errors))
  if len(no_data) > 0:
    with open(f"sin_datos.txt", "w") as output:
          output.write('\n'.join(no_data))
main()