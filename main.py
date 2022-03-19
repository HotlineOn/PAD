import PySimpleGUI as sg
from PAD_backend import *

DEFAULT_PATH = os.getcwd()
MAX_NUM_OF_ARTICLES = {'IAD': 1000, 'NOT IAD': 1200}
config = get_config()
if config:
    DEFAULT_PATH = config['DEFAULT PATH']


def articles_window(path_file_articles: str, preview_num: int) -> None:
    articles = get_random_articles(load_binary(path_file_articles), preview_num)
    output_text = ''
    for article in articles:
        output_text += 'Название: ' + article['title'] + '\n' + \
                       'Темы: ' + ', '.join(article['tags']['names']) + '\n' + \
                       'Описание: ' + article['abstract'] + '\n' + \
                       'Дата публикации: ' + article['submitted'] + '\n\n\n'
    preview_layout = [
        [sg.Multiline(output_text, size=(100, 30), disabled=True)],
        [sg.Submit('ОК')]
    ]

    preview = sg.Window('Предпросмотр Статей', preview_layout)

    while True:
        event, _ = preview.read()
        if event == 'ОК' or event == sg.WIN_CLOSED:
            break

    preview.close()


def options_window() -> None:
    options_layout = [
        [
            sg.Column([
                [sg.Text('Какие данные:')],
                [
                    sg.Radio('ИАД', 'RADIO1', default=True, key='-IS IAD-'),
                    sg.Radio('не ИАД', 'RADIO1', default=False)
                ],
            ])
        ],
        [
            sg.Column([
                [sg.Text('Рабочая директория:')],
                [
                    sg.InputText(default_text=DEFAULT_PATH, key='-PATH-'),
                    sg.FolderBrowse(enable_events=True, key='-F-', target='-F-')
                ],
                [sg.Checkbox('сделать путём по умолчанию', key='-CHANGE DEFAULT PATH-')],
                [sg.Checkbox('удалить существующие файлы по текущей категории', key='-WILL DELETE-',
                             enable_events=True)],
                [sg.T('')],
            ])
        ],
        [
            sg.Column([
                [sg.Text('Загрузка данных:')],
                [
                    sg.Radio('с сайта', 'RADIO2', default=True, key='-FROM ELIB-', enable_events=True),
                    sg.Radio('из файла', 'RADIO2', default=False, key='-FROM FILE-',
                             enable_events=True, disabled=False),
                    sg.Radio('из файла статей', 'RADIO2', default=False, key='-FROM FILE ARTICLES-',
                             enable_events=True, disabled=False)
                ],
                [sg.Column([
                    [
                        sg.Text('Количество статей на странице:'),
                        sg.OptionMenu([200, 100, 50], 200, key='-ARTICLES PER PAGE-')
                    ],
                    [sg.Text('Количество страниц:'), sg.InputText('1', 5, key='-NUM OF PAGES-')],
                ], key='-FROM ELIB MENU-', visible=True)]
            ])
        ],
        [
            sg.Column([
                [sg.Checkbox('предпросмотр', default=True, key='-ON SCREEN-', enable_events=True)],
                [sg.Text('Количество статей в окне предпросмотра: '), sg.InputText('3', 5, key='-ARTICLES TO PREVIEW-')]
            ])
        ],
        [sg.Text('', text_color='orange red', key='-FILE NOTIFICATION-')],
        [
            sg.Submit('Принять'),
            sg.Cancel('Отмена')
        ]
    ]

    right_path = DEFAULT_PATH
    window = sg.Window('ПАД', options_layout)

    while True:
        event, values = window.read()
        if event not in (None, 'Exit', 'Отмена', 'Принять'):
            window['-FILE NOTIFICATION-'].update('')
        if event in (None, 'Exit', 'Отмена'):
            break
        elif event == '-F-':
            window['-PATH-'].update(values['-F-'].replace('/', '\\'))
        elif event == '-WILL DELETE-':
            if values['-WILL DELETE-']:
                window['-FROM FILE-'].update(disabled=True)
                window['-FROM FILE ARTICLES-'].update(disabled=True)
                window['-FROM ELIB-'].update(True)
                window['-FROM ELIB MENU-'].unhide_row()
            else:
                window['-FROM FILE-'].update(disabled=False)
                window['-FROM FILE ARTICLES-'].update(disabled=False)
        elif event == '-FROM ELIB-':
            window['-FROM ELIB MENU-'].unhide_row()
        elif event == '-FROM FILE-':
            window['-FROM ELIB MENU-'].hide_row()
        elif event == '-FROM FILE ARTICLES-':
            window['-FROM ELIB MENU-'].hide_row()
        elif event == '-ON SCREEN-':
            if values['-ON SCREEN-'] is True:
                window['-ARTICLES TO PREVIEW-'].unhide_row()
            else:
                window['-ARTICLES TO PREVIEW-'].hide_row()
        elif event == 'Принять':
            folder_path = values['-PATH-']
            if not os.path.exists(folder_path):
                sg.PopupError('Такого пути несуществует!', title='', text_color='white', keep_on_top=True)
                window['-PATH-'].update(right_path)
                continue
            else:
                right_path = values['-PATH-']

            is_iad = values['-IS IAD-']
            file_html = 'IAD_html.bin' if is_iad else 'NOT_IAD_html.bin'
            file_articles = 'IAD.bin' if is_iad else 'NOT_IAD.bin'
            articles_per_page = 0
            num_of_pages = int(values['-NUM OF PAGES-'])
            path_html_exists = os.path.exists(folder_path + '\\' + file_html)
            path_articles_exists = os.path.exists(folder_path + '\\' + file_articles)
            from_elib = values['-FROM ELIB-']
            if not path_articles_exists and not path_html_exists and not from_elib:
                window['-FILE NOTIFICATION-'].update('Файлы не найдены!', text_color='orange red')
                window['-FROM FILE ARTICLES-'].update(disabled=True)
                window['-FROM FILE-'].update(disabled=True)
                window['-FROM ELIB-'].update(True)
                window['-FROM ELIB MENU-'].unhide_row()
                continue
            elif not path_articles_exists and values['-FROM FILE ARTICLES-']:
                window['-FILE NOTIFICATION-'].update('Файл не найден!', text_color='orange red')
                window['-FROM FILE ARTICLES-'].update(disabled=True)
                window['-FROM FILE-'].update(disabled=False)
                continue
            elif not path_html_exists and values['-FROM FILE-']:
                window['-FILE NOTIFICATION-'].update('Файл не найден!', text_color='orange red')
                window['-FROM FILE ARTICLES-'].update(disabled=False)
                window['-FROM FILE-'].update(disabled=True)
                continue
            elif from_elib:
                try:
                    articles_per_page = int(values['-ARTICLES PER PAGE-'])
                except ValueError:
                    sg.PopupError('Введите число в поле Количество статей')
                    continue
                else:
                    request_option_size = len(IAD_OPTIONS) if is_iad else len(NOT_IAD_OPTIONS)
                    max_num_of_articles = MAX_NUM_OF_ARTICLES['IAD'] if is_iad else MAX_NUM_OF_ARTICLES['NOT IAD']
                    num_of_articles = request_option_size * articles_per_page * num_of_pages
                    if num_of_articles < 50 or num_of_articles > max_num_of_articles:
                        error_text = 'Максимальное число считываемых страниц\n' + \
                                     'для количества статей на странице = ' + str(articles_per_page) + ':\n' + \
                                      str(int(max_num_of_articles / articles_per_page / request_option_size))
                        sg.PopupError(error_text, title='', text_color='white', keep_on_top=True)
                        continue

                if values['-WILL DELETE-']:
                    window['-WILL DELETE-'].update(False)
                window['-FROM FILE ARTICLES-'].update(True, disabled=False)
                window['-FROM FILE-'].update(disabled=False)
                window['-FROM ELIB MENU-'].hide_row()
                window['-FILE NOTIFICATION-'].update('Файлы успешно сохранены!', text_color='green2')

            else:
                window['-FILE NOTIFICATION-'].update('Файл успешно сохранён!', text_color='green2')

            try:
                preview_num = int(values['-ARTICLES TO PREVIEW-'])
            except ValueError:
                sg.PopupError('Введите число от 1 до 50', title='', text_color='white', keep_on_top=True)
                continue
            else:
                if preview_num < 1 or preview_num > 50:
                    sg.PopupError("""В поле Количество статей в окне предпросмотра:
                                Введите число от 1 до 50""", title='', text_color='white', keep_on_top=True)
                    continue

            delete_binary = values['-WILL DELETE-']
            change_default_path = values['-CHANGE DEFAULT PATH-']
            on_screen = values['-ON SCREEN-']

            if change_default_path:
                set_config({'DEFAULT PATH': folder_path})
            os.chdir(folder_path)
            if delete_binary:
                if os.path.exists(file_html):
                    delete_file(file_html)
                if os.path.exists(file_articles):
                    delete_file(file_articles)

            if from_elib:
                download(make_urls(is_iad, articles_per_page, num_of_pages), file_html)
                dump_binary(file_articles, parse(file_html))
            elif values['-FROM FILE-']:
                dump_binary(file_articles, parse(file_html))

            if on_screen:
                articles_window(folder_path + '\\' + file_articles, preview_num)

    window.close()


if __name__ == '__main__':
    options_window()
