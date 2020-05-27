from datetime import datetime

def build_url(base, paths, param_dict):
    path_string = ''
    param_string = '?'

    for path in paths:
        path_string += path + '/'
    path_string = path_string.rstrip('/')
    
    for k, v in param_dict.items():
        param_string += k + '=' + v + '&'
    param_string = param_string.rstrip('&')
        
    return base + path_string + param_string

def convert_to_unix(date):
    return str(1000 * int(datetime.strptime(date, "%Y-%m-%d").timestamp()))