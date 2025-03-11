from telebot.callback_data import CallbackData

categories_factory = CallbackData(
    'label',
    'action',
    'argument',
    prefix='categories',
)
actions_factory = CallbackData(
    'action',
    'p',
    's',
    'a',
    'u',
    'c',
    'e',
    prefix='actions',
)
