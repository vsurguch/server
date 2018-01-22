

SERVER_MAIN_MENU = {
    '1': 'Log',
    '2': 'All clients in database',
    '3': 'Connected clients',
    'q': 'Quit',
}

def menu(menu_dict):
    for n, text in menu_dict.items():
        print('{}. {}'.format(n, text))
    selection = input('Select command:')
    return selection
