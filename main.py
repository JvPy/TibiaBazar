import requests # Biblioteca para fazer requisições HTTP (acessar páginas web).
from bs4 import BeautifulSoup # Biblioteca para analisar (parsear) o HTML da página e navegar por ele.
import csv # Módulo para ler e escrever arquivos CSV (formato de tabela).
import re # Módulo para usar Expressões Regulares (RegEx), essencial para extrair textos específicos.
import time # Módulo para pausar a execução (evita sobrecarregar o servidor).
from urllib.parse import urlunsplit, urlencode # Ferramentas para construir URLs complexas de forma segura.

# ----------------------------------------------------------------------
# --- 0. Configuração: Parâmetros, URL Base e Paginação ---
# ----------------------------------------------------------------------

BASE_SCHEME = 'https' # O protocolo de segurança (sempre 'https').
BASE_NETLOC = 'www.tibia.com' # O domínio do site.
BASE_PATH = '/charactertrade/' # O caminho específico dentro do domínio.
BASE_QUERY = 'subtopic=pastcharactertrades' # A primeira parte da consulta URL (fixa).

# Parâmetros de Filtro (fácil de alterar aqui sem mudar o URL gigante!)
# Se você quiser filtrar por outra vocação, mude 'filter_profession'.
QUERY_PARAMS = {
    'filter_profession': '0', # 0 = Todas as vocações
    'filter_levelrangefrom': '0',
    'filter_levelrangeto': '0',
    'filter_world': '',
    'filter_worldpvptype': '9',
    'filter_worldbattleyestate': '1',
    'filter_skillid': '1',
    'filter_skillrangefrom': '1',
    'filter_skillrangeto': '100',
    'order_column': '101',
    'order_direction': '1',
    # 'currentpage' será adicionado a este dicionário a cada loop.
}

START_PAGE = 1 # Página inicial do scraping.
END_PAGE = 50 # Última página a ser raspada.
output_filename = 'tibia_auction_data_final.csv' # Nome do arquivo de saída.

# ----------------------------------------------------------------------
# --- HEADERS, CHAVES DE EXTRAÇÃO E REGEX ---
# ----------------------------------------------------------------------

# Nomes das colunas no arquivo CSV final.
CSV_HEADERS = [
    'Level', 'Vocation', 'World', 'Minimum Bid', 'Winning Bid',
    'Magic Level', 'Auction Start Date', 'Auction End Date'
]

# Expressões Regulares (RegEx) para encontrar e capturar os dados.
# O texto dentro de parênteses é o que será CAPTURADO (grupo 1).
regex_patterns = {
    'Level': r'Level:\s*(\d+)', # Captura um ou mais dígitos (\d+) após 'Level:'.
    'Vocation': r'Vocation:\s*(.+?)\s*\|', # Captura qualquer coisa (.+?) não-gananciosa até o '|'.
    # LOOKAHEAD (?=...): Captura o World, mas para ANTES de 'Auction Start:'.
    'World': r'World:\s*(.*?)(?=Auction Start:)',
    'Minimum Bid': r'Minimum Bid:\s*([\d,]+)', # Captura dígitos e vírgulas (preço).
    'Winning Bid': r'Winning Bid:\s*([\d,]+)',
    'Magic Level': r'(\d+)\s*Magic Level', # Captura os dígitos que aparecem antes de 'Magic Level'.
    # Captura a data/hora até 'CEST' ou 'Auction End:'.
    'Auction Start Date': r'Auction Start:(.*?)(?=CEST|Auction End:)', 
    # Captura a data/hora até 'CEST' ou o label que vem antes de 'Minimum Bid:'.
    'Auction End Date': r'Auction End:(.*?)(?=CEST|(\w+\s*)?Minimum Bid:)' 
}

# Lista de chaves na ORDEM EXATA em que queremos os dados no CSV.
KEYS_TO_EXTRACT = [
    'Level', 'Vocation', 'World', 'Minimum Bid', 'Winning Bid',
    'Magic Level', 'Auction Start Date', 'Auction End Date'
]

# Onde armazenamos os dados. Usamos um SET para garantir que cada linha seja única!
unique_rows_data = set() 
total_tr_found = 0 # Contador total de linhas encontradas para o relatório final.

# ----------------------------------------------------------------------
# --- MAIN PAGINATION LOOP (Laço Principal de Paginação) ---
# ----------------------------------------------------------------------

# Itera por cada número de página, de START_PAGE a END_PAGE.
for page in range(START_PAGE, END_PAGE + 1):
    
    # 1. Construir a URL Dinamicamente
    current_params = QUERY_PARAMS.copy() # Cria uma cópia dos filtros base.
    current_params['currentpage'] = str(page) # Adiciona o número da página atual.
    
    # Converte o dicionário de filtros em uma string de URL (ex: 'filtro=X&filtro=Y').
    encoded_params = urlencode(current_params)
    
    # Junta a consulta base ('subtopic...') com os parâmetros codificados.
    full_query = f"{BASE_QUERY}&{encoded_params}"
    
    # Monta o URL completo a partir de todas as partes (esquema, domínio, caminho, consulta).
    url = urlunsplit((BASE_SCHEME, BASE_NETLOC, BASE_PATH, full_query, ''))
    
    print(f"Scraping page {page}...")
    
    # 2. Requisitar e Analisar (Parsear) o HTML
    try:
        response = requests.get(url) # Faz a requisição HTTP.
        response.raise_for_status() # Checa por erros 4xx/5xx (ex: página não encontrada).
    except requests.exceptions.RequestException as e:
        print(f"Error fetching page {page}: {e}. Stopping pagination.")
        break # Para o loop em caso de erro.
    
    # Verifica se o conteúdo está vazio (pode indicar o fim das páginas).
    if not response.content.strip():
        print(f"Page {page} returned empty content. Stopping.")
        break

    soup = BeautifulSoup(response.content, 'html.parser') # Transforma o HTML em um objeto navegável.

    # 3. Encontrar a Tabela Correta (o Segundo Container)
    all_tables = soup.find_all('div', class_='InnerTableContainer') # Busca TODAS as DIVs com a classe.

    if len(all_tables) < 2:
        print(f"Fewer than two InnerTableContainer divs found on page {page}. Stopping.")
        break
    
    second_table_div = all_tables[1] # Seleciona o SEGUNDO elemento da lista (índice 1).
    all_tr_elements = second_table_div.find_all('tr') # Encontra todas as linhas (<tr>) dentro dessa DIV.
    total_tr_found += len(all_tr_elements)

    # 4. Processar Linhas e Extrair Dados
    for tr in all_tr_elements:
        tds = tr.find_all(['th', 'td']) # Encontra todas as células (<th> e <td>) da linha.
        # Concatena o texto de todas as células em uma string para facilitar o RegEx.
        full_row_text = ' '.join([cell.get_text(separator=' ', strip=True) for cell in tds])
        
        extracted_data = {}
        for key, pattern in regex_patterns.items():
            match = re.search(pattern, full_row_text) # Tenta encontrar o padrão RegEx na string.
            if match:
                raw_value = match.group(1).strip() # Pega apenas o que está entre parênteses no RegEx.
                extracted_data[key] = raw_value
                
                # Limpeza adicional para Campos de Data (retira hora e fuso horário)
                if key in ['Auction Start Date', 'Auction End Date']:
                    date_parts = raw_value.split()
                    if len(date_parts) >= 3:
                        # Junta apenas as 3 primeiras partes (Mês Dia Ano) e remove vírgulas.
                        extracted_data[key] = ' '.join(date_parts[:3]).replace(',', '') 
                    else:
                        extracted_data[key] = 'N/A' # Fallback se a data estiver incompleta.
            else:
                extracted_data[key] = 'N/A' # Se o RegEx não encontrar nada, preenche com 'N/A'.

        # Cria uma lista de dados na ordem correta do CSV.
        data_list = [extracted_data[key] for key in KEYS_TO_EXTRACT]
        
        # Garante que apenas linhas com Level ou Minimum Bid válido sejam consideradas (ignora linhas vazias/header).
        if extracted_data['Level'] != 'N/A' or extracted_data['Minimum Bid'] != 'N/A':
            # Converte a lista para tupla (imutável) e adiciona ao SET (garante exclusividade).
            unique_rows_data.add(tuple(data_list))

    time.sleep(1) # Pausa de 1 segundo para ser educado com o servidor do site.

# ----------------------------------------------------------------------
# --- 5. Exportar Dados Únicos para CSV ---
# ----------------------------------------------------------------------

if unique_rows_data:
    data_to_write = list(unique_rows_data) # Converte o SET de volta para uma lista para escrever no CSV.

    try:
        # Abre o arquivo CSV para escrita ('w'), usa 'newline=""' para evitar linhas em branco extras.
        with open(output_filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(CSV_HEADERS) # Escreve a linha de cabeçalho.
            writer.writerows(data_to_write) # Escreve todas as linhas de dados de uma vez.

        print("-" * 40)
        print("✅ **PAGINATED SCRAPING COMPLETE.**")
        print(f"   Páginas raspadas: {START_PAGE} a {page if page != END_PAGE+1 else END_PAGE}.")
        print(f"   Total de linhas <tr> encontradas: {total_tr_found}")
        print(f"   Linhas únicas escritas no CSV: {len(data_to_write)}")
        print(f"   Arquivo de Saída: {output_filename}")
        print("-" * 40)

    except IOError as e:
        print(f"Erro ao escrever no arquivo {output_filename}: {e}")
else:
    print("Nenhuma linha de dados significativa foi extraída para escrita.")