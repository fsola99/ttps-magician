import requests
from bs4 import BeautifulSoup
import openpyxl

lista_ids = []
last_technique = ""
dic_final = {}

# Función para obtener la información de una técnica o sub-técnica
def obtener_info(item, souper):
    title = souper.find("h1")
    title_name = title.text.strip()
    
    if ":" in title_name:    
        title_splitted = title_name.split(":")
        sin_espacio = title_splitted[1].lstrip()
    
        title_final = title_splitted[0] + " " + sin_espacio
    else:
        title_final = title_name
    
    print(title_final)
    
    description = souper.find("div", {"class": "description-body"})
    description_text = description.text.strip() if description else 'No description available'
    
    #Plataformas
    divs_plataformas = souper.find_all('div', class_='row card-data')
    # Iterar sobre los divs de las plataformas
    for div_plataformas in divs_plataformas:
        # Encontrar el span que contiene el título 'Platforms:'
        span_titulo = div_plataformas.find('span', class_='h5 card-title')
    
        if span_titulo and span_titulo.text.strip() == 'Platforms:':
            # Obtener el valor de las plataformas
            plataformas_feo = div_plataformas.find('div', class_='col-md-11 pl-0').text.strip() #Platforms: Azure AD, Google Workspace, IaaS, Linux, Office 365, SaaS, Windows, macOS
            plataformas=plataformas_feo[11:]
    
    dic_final[item] = {
        'name': title_final,
        'description': description_text,
        'platforms': plataformas,
    }

# Función para guardar los datos en un archivo Excel
def guardar_en_excel(diccionario, nombre_archivo):
    # Crear un nuevo libro de trabajo y una hoja
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Técnicas MITRE"

    # Escribir la fila de encabezado
    ws.append(["ID", "Title", "Description", "Platforms"])

    # Escribir cada fila con la información de dic_final
    for key, value in diccionario.items():
        ws.append([key, value['name'], value['description'], value['platforms']])

    # Guardar el archivo Excel
    wb.save(nombre_archivo)
    print(f"Archivo Excel guardado como {nombre_archivo}")

# ---------------------- RECORRER MITRE ----------------------------------------

url = 'https://attack.mitre.org/techniques/enterprise/'

# Realizar la solicitud HTTP GET a la página
response = requests.get(url)

# Verificar si la solicitud fue exitosa
if response.status_code == 200:
    # Crear un objeto BeautifulSoup con el contenido HTML de la página
    soup = BeautifulSoup(response.content, 'html.parser')

    # Encontrar la tabla que contiene las técnicas
    table = soup.find('table', {"class": "table-techniques"})

    # Verificar si la tabla existe
    if table:
        # Recorrer todas las filas de la tabla
        rows = table.find_all("tr")
        
        for row in rows:
            # Verificar si la fila es una técnica principal
            if "technique" in row.get('class', []) and "sub" not in row.get('class', []):
                # Obtener el ID de la técnica
                id_cell = row.find('td')  # Asumimos que la segunda celda tiene el ID
                if id_cell:
                    technique_id = id_cell.text.strip()  # Obtener el ID de la técnica (por ejemplo, T1458)

                    last_technique = technique_id
                    # Guardar la técnica en la lista
                    lista_ids.append(technique_id)
            elif "sub" in row.get('class', []):
                subtech_id_cell = row.find_all('td')[1]
                subtech_id = subtech_id_cell.text.strip()
                lista_ids.append(last_technique + subtech_id)
    print(lista_ids)

# Procesar cada técnica y sub-técnica
for item in lista_ids:
    if '.' not in item:
        url_id = "https://attack.mitre.org/techniques/" + item + "/"
        print(url_id)
        # Realizar la solicitud HTTP GET a la página
        response_tec = requests.get(url_id)
        if response_tec.status_code == 200:
            soup_tec = BeautifulSoup(response_tec.content, 'html.parser')
            obtener_info(item, soup_tec)
        else:
            print("No pude obtener técnica:", item)              
    else:
        x = item.split(".")
        url_sub_id = "https://attack.mitre.org/techniques/" + x[0] + "/" + x[1]
        # Realizar la solicitud HTTP GET a la página
        response_sub = requests.get(url_sub_id)
        if response_sub.status_code == 200:
            soup_sub = BeautifulSoup(response_sub.content, 'html.parser')
            obtener_info(item, soup_sub)
        else:
            print("No pude obtener sub-técnica:", item)      

# Guardar los resultados en un archivo Excel
print(dic_final)
guardar_en_excel(dic_final, "ttps.xlsx")
