# ⚔️ Web Scraper de Leilões de Personagens Tibia

Este script Python foi desenvolvido para raspar (scraping) dados de leilões de personagens finalizados no site oficial do Tibia. Ele usa paginação automática para coletar dados de múltiplas páginas e salva o resultado em um arquivo CSV limpo, garantindo que não haja linhas duplicadas.

## ✨ Funcionalidades

* **Paginação Automática:** Raspa de forma sequencial um intervalo configurável de páginas (padrão: 1 a 50).
* **Gestão de URL:** Constrói URLs dinamicamente a partir de um dicionário de filtros (vocação, nível, mundo, etc.).
* **Extração de Dados:** Utiliza **Expressões Regulares (RegEx)** para extrair dados específicos e limpos (Nível, Vocação, Mundo, Lances, Datas, etc.) de strings de texto complexas.
* **Desduplicação:** Usa um `set` para garantir que cada linha exportada para o CSV seja única.
* **Comportamento Educado:** Inclui um pequeno atraso (`time.sleep(1)`) entre as requisições para evitar sobrecarregar o servidor do Tibia.

***

## 🛠️ Requisitos

Você precisará ter o **Python 3** instalado em sua máquina.

### Instalação de Dependências

Todas as bibliotecas necessárias estão listadas no arquivo `requirements.txt`. Instale-as usando o `pip` (gerenciador de pacotes do Python):

1.  **Crie um Ambiente Virtual** (recomendado para isolamento de projetos):
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # No Linux/macOS
    .\venv\Scripts\activate   # No Windows
    ```

2.  **Instale as bibliotecas** listadas no `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```

***

## ⚙️ Configuração

Todos os parâmetros de filtro e paginação podem ser ajustados diretamente no início do script.

### Filtros da URL

Edite o dicionário `QUERY_PARAMS` no topo do script para alterar os critérios de busca, como o ID da vocação (`filter_profession`) ou o intervalo de nível:

```python
QUERY_PARAMS = {
    'filter_profession': '0',   # 0 = Todas as vocações, 5 = Elite Knight, etc.
    'filter_levelrangefrom': '0',
    # ... outros filtros ...
}