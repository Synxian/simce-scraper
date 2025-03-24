import requests
import json
import rarfile
import os

def get_all_schools_json():
    url = "https://www.agenciaeducacion.cl/wp-content/themes/ace-child/data/establecimientos.json"
    response = requests.get(url)
    data = response.json()
    with open("establecimientos.json", "w") as f:
        json.dump(data, f)

def get_enrollments_csv():
    url = "https://datosabiertos.mineduc.cl/wp-content/uploads/2025/01/Resumen_Matricula_EE_2024.rar"
    response = requests.get(url)
    with open("tmp.rar", "wb") as f:
        f.write(response.content)
    with rarfile.RarFile("tmp.rar") as rf:
        for f in rf.infolist():
            if f.filename.endswith('.csv'):
                with open('matriculas.csv', 'wb') as out_file:
                    out_file.write(rf.read(f))
                break

    os.remove("tmp.rar")

def get_ive_file():
    url = "https://www.junaeb.cl/wp-content/uploads/2024/04/IVE-2024.xlsx"
    response = requests.get(url, verify=False)
    with open("IVE.xlsx", "wb") as f:
        f.write(response.content)

def main():
    get_all_schools_json()
    get_enrollments_csv()
    get_ive_file()

if __name__ == "__main__":
    main()
