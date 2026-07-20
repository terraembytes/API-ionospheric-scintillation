import itertools
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import math

dict_constellations = {
    'ALL': range(1, 177),
    'GPS': range(1, 37),
    'GLONASS': range(38, 68),
    'GALILEO': range(71, 102),
    'BeiDou': range(141, 177)
}

interval_map = {
        '1 minuto': '1min',
        '5 minutos': '5min',
        '10 minutos': '10min',
        '30 minutos': '30min',
        '1 hora': '60min',
        '2 horas': '120min',
        '3 horas': '180min',
        '4 horas': '240min',
    }

# filtro geral da constelação e elevação
def filter_constella_elev(dados, constellation, elev, elevType) -> list[dict]:
    print("Filtrando por constelação...")
    if constellation != 'ALL':
        data_filtered1 = constellation_filter(constellation, dados)
    else:
        data_filtered1 = dados
    print("Filtrando a elevação...")
    return elevation_filter(elev, elevType, data_filtered1)

# agrupando por contagem de S4
def group_s4(data_copy: list[dict], constellation: str, time: str) -> list[dict]:
    df = pd.DataFrame(data_copy)
    if constellation == 'ALL':
        list_df = [] # lista que vai receber todos os df
        # pegando cada constelação e fazendo o agrupameto, para depois juntar tudo
        # Este for pega a chave e valor no dicionario atraves do .items()
        # Começa a partir da posição 1
        for constella, ranges in itertools.islice(dict_constellations.items(), 1, None):
            list_df.append(group_time_s4(df, ranges, time))
        df_complete = pd.concat(list_df, ignore_index=True)
    else:
        df_complete = constellation_time_s4(df, time)
    # convertendo o DataFrame em list[dict]
    return df_complete.to_dict(orient='records')

# operação semelhante a função group_time_s4, mas trabalha com apenas uma constelação
def constellation_time_s4(df, time) -> pd.DataFrame:
    freq = interval_map[time] # pegando o tempo escolhido pelo usuario

    df_cut = df.copy()
    # tratatando rapidamente os dados
    df_cut['Date'] = pd.to_datetime(df_cut['Date'])
    df_cut['S4'] = pd.to_numeric(df_cut['S4'], errors='coerce').fillna(0)

    df_cut['time_group'] = df_cut['Date'].dt.ceil(freq)

    grouped = df_cut.groupby('time_group')['S4'].agg([
        ('s4_06', lambda x: (x >= 0.6).sum()),
        ('s4_03', lambda x: (x.between(0.3, 0.6, inclusive='left')).sum())
    ]).reset_index()

    df_group_cut = pd.DataFrame({
        'Date': grouped['time_group'],
        'S4_06': grouped['s4_06'],
        'S4_03': grouped['s4_03']
    })
    # Otimiza o df para que uma unica coluna contenha os dois valores de s4
    df_cut_long = pd.melt(df_group_cut, id_vars='Date', var_name='S4', value_name='Quantidade')
    return df_cut_long

# realiza a operação de agrupamento em si
def group_time_s4(df, ranges, time) -> pd.DataFrame:
    # obtendo o DataFrame de cada constelação
    df_cut = df.loc[df['Svid'].isin(ranges), :].copy()
    df_cut['Date'] = pd.to_datetime(df_cut['Date'])
    df_cut['S4'] = pd.to_numeric(df_cut['S4'], errors='coerce').fillna(0)
    freq = interval_map[time]
    # na nova coluna 'time_group', eu adiciono o tempo arredondando para a proxima freq
    # dessa forma, posteriormente, é possivel calcular os valores agrupando pelo 'time_group'
    df_cut['time_group'] = df_cut['Date'].dt.ceil(freq)
    # cria um DataFrameGroupby com o calculo da somatoria dos valores de S4
    grouped = df_cut.groupby('time_group')['S4'].agg([
        ('s4_06', lambda x: (x >= 0.6).sum()),
        ('s4_03', lambda x: (x.between(0.3, 0.6, inclusive='left')).sum())
    ]).reset_index()
    # transforma o grouped em um DataFrame padrao com tres colunas
    df_group_cut = pd.DataFrame({
        'Date': grouped['time_group'],
        'S4_06': grouped['s4_06'],
        'S4_03': grouped['s4_03']
    })
    # Otimiza o df para que uma unica coluna contenha os dois valores de s4
    df_cut_long = pd.melt(df_group_cut, id_vars='Date', var_name='S4', value_name='Quantidade')
    return df_cut_long

# filtro das constelações de satélite
def constellation_filter(constellation: str, dados: list[dict]) -> list[dict]:
    values = dict_constellations.get(constellation, [])
    data_copy = [linha for linha in dados if int(linha.get('Svid') or 0) in values]
    return data_copy

# filtro da elevação
def elevation_filter(elev: int, elevType: int, data_copy: list[dict]) -> list[dict]:
    data_pre_processed = [{**linha, 'Elevation': int(linha.get('Elevation') or 0)} for linha in data_copy]
    match elevType:
        case 1:
            data_processed = [linha for linha in data_pre_processed if int(linha['Elevation']) >= elev]
            print(f"Filtrando a elevação >= {elev}")
        case 2:
            data_processed = [linha for linha in data_pre_processed if int(linha['Elevation']) <= elev]
            print(f"Filtrando a elevação <= {elev}")
        case 3:
            data_processed = [linha for linha in data_pre_processed if int(linha['Elevation']) == elev]
            print(f"Filtrando a elevação == {elev}")
        case 4:
            data_processed = [linha for linha in data_pre_processed if int(linha['Elevation']) > elev]
            print(f"Filtrando a elevação > {elev}")
        case 5:
            data_processed = [linha for linha in data_pre_processed if int(linha['Elevation']) < elev]
            print(f"Filtrando a elevação < {elev}")
        case _:
            data_processed = data_pre_processed
            print("tipo de filtro invalido")
    return data_processed

# função para cortar um pedaço baseado num horário
def cut_hour_range(hour_range: int | None, hour_selected: str | None, data_copy) -> list[dict]:
    if hour_range is None or hour_selected is None:
        return data_copy
    
    hour_selected = datetime.strptime(hour_selected, '%Y-%m-%d %H:%M:%S')
    future_date = hour_selected + timedelta(hours=hour_range)
    new_df = pd.DataFrame(data_copy)
    new_df['Date'] = pd.to_datetime(new_df['Date'])
    mask = (new_df['Date'] >= hour_selected) & (new_df['Date'] <= future_date)
    data_cut = new_df.loc[mask].copy()
    data_list = data_cut.to_dict(orient='records')
    return data_list

def convert_str_to_float(data: list[dict], indice: str):
    return list(map(lambda x: {**x, indice: float(x[indice])}, data))

def convert_str_to_int(data: list[dict], indice: str) -> list[dict]:
    df = pd.DataFrame(data)
    df[indice] = pd.to_numeric(df[indice], errors='coerce').fillna(0)
    return df.to_dict(orient='records')

def convert_number_to_str(data: list[dict], indice):
    return list(map(lambda x: {**x, indice: str(x[indice])}, data))

# função para filtrar pelo indice S4
def get_s4_higher_equals(s4_value, data: list[dict]) -> list[dict]:
    return filter(lambda x: x['S4'] >= s4_value, data)

# funcao para converter o azimute para radianos
def transform_to_radian(data: list[dict]) -> list[dict]:
    return list(map(lambda x: {**x, 'Azimute': np.radians(x['Azimute'])}, data))

# funcao para definir o tamanho de cada plot baseado no S4
def add_size_s4(data: list[dict]):
    list_size = []
    for item in data:
        if item['S4'] < 0.6:
            list_size.append('10')
        elif item['S4'] >= 0.6 and item['S4'] < 1:
            list_size.append('20')
        elif item['S4'] >= 1 and item['S4'] < 1.2:
            list_size.append('35')
        else:
            list_size.append('45')
    df = pd.DataFrame(data)
    df['sizePlot'] = list_size
    return df.to_dict(orient='records')

# funcao para definir a opacidade de cada plot baseado no S4
def add_opacity_s4(data: list[dict]):
    list_alpha = []
    for item in data:
        if item['S4'] < 0.6:
            list_alpha.append('0.05')
        elif item['S4'] >= 0.6 and item['S4'] < 1:
            list_alpha.append('0.5')
        elif item['S4'] >= 1 and item['S4'] < 1.2:
            list_alpha.append('0.8')
        else:
            list_alpha.append('1')
    df = pd.DataFrame(data)
    df['alphaPlot'] = list_alpha
    return df.to_dict(orient='records')

def remover_s4_nan(data: list[dict]):
    processed_data = [linha for linha in data if linha['S4'] != 'NaN' and linha['S4'] != '']
    return processed_data

def remover_svid_nan(data: list[dict]):
    df = pd.DataFrame(data)
    df['Svid'] = pd.to_numeric(df['Svid'], errors='coerce').fillna(0).astype(int)
    processed_data = df.to_dict(orient='records')
    return processed_data

# funcao para encontrar a(s) constelação(ões) com maior quantidade de satelites com s4 alto
def find_constellations_higher_s4(data: list[dict]):
    all_constellations = {
        range(1, 37): 'GPS',
        range(38, 68): 'GLONASS',
        range(71, 102): 'GALILEO',
        range(141, 177): 'BeiDou'
    }

    df = pd.DataFrame(data)

    highest_svid = df['Svid'].value_counts().max()

    most_frequent_all = df['Svid'].value_counts()[lambda x: x == highest_svid].index.tolist()
    constellations = [
        all_constellations[svid] for svid in most_frequent_all
    ]

    unique_constellations = list(set(constellations))
    return unique_constellations

# funcao para encontrar a hora com maior quantidade de satelites com s4 alto
def get_hour_higher_s4_values(data: list[dict]):
    df = pd.DataFrame(data)
    df['hora_exata'] = df['Date'].dt.time

    hours_count = df['hora_exata'].value_counts()

    critical_hour = hours_count.index[0]
    return critical_hour