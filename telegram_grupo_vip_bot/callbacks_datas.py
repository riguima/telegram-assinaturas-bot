from telebot.callback_data import CallbackData

plans_factory = CallbackData(
    'action',
    'argument',
    prefix='plans',
)
actions_factory = CallbackData(
    'action',
    'p',
    's',
    'u',
    'e',
    prefix='actions',
)
