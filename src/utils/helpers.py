def verificar_parametros_iguais(param: dict, start, end, station) -> bool:
    if param.get('start') == start and param.get('end') == end and param.get('station') == station:
        res = True
    else:
        res = False
    return res
