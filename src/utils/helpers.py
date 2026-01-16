import itertools
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

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

def verificar_parametros_iguais(param: dict, start, end, station) -> bool:
    if param.get('start') == start and param.get('end') == end and param.get('station') == station:
        res = True
    else:
        res = False
    return res

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
    df_cut['S4'] = df_cut['S4'].replace('NaN', np.nan)
    df_cut['S4'] = pd.to_numeric(df_cut['S4'])

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
    df_cut['S4'] = df_cut['S4'].replace('NaN', np.nan)
    df_cut['S4'] = pd.to_numeric(df_cut['S4'])
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
    data_copy = [linha for linha in dados if linha.get('Svid') in values]
    return data_copy

# filtro da elevação
def elevation_filter(elev: int, elevType: int, data_copy: list[dict]) -> list[dict]:
    data_pre_processed = [{**linha, 'Elevation': linha.get('Elevation') or 0} for linha in data_copy]
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
            data_processed = [linha for linha in data_pre_processed if int(linha['Elevation']) >= elev]
            print(f"Filtrando a elevação < {elev}")
        case _:
            data_processed = []
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