"""Aggregate every user-available command."""
import dataset
from telegram import Bot, Update
from telegram.ext import CommandHandler
from babel.dates import format_date
from babel.numbers import format_number, format_decimal

from . import analytics
from .config import DB_URI, set_locale, LOCALE
from .util import get_period, user_info_from_message_or_reply, user_info_from_username

set_locale()


def average_length(bot: Bot, update: Update):
    """Reply the user who invoked the command with hers/his average message length.

    Args:
        bot: The object that represents the Telegram Bot.
        update: The object that represents an incoming update for the bot to handle.
    """

    average = analytics.average_message_length(
        update.message.from_user.id, update.message.chat.id
    )
    response = f'{format_decimal(average, locale=LOCALE)}'

    update.message.reply_text(response)


def karma(bot: Bot, update: Update):
    """Reply the user who invoked the command with hers/his respective karma.

    Args:
        bot: The object that represents the Telegram Bot.
        update: The object that represents an incoming update for the bot to handle.
    """
    db = dataset.connect(DB_URI)

    message = update.message
    text = message.text

    cmd, *args = text.split()

    username = None
    period = get_period(_('m'))
    if args:
        periods = [_('w'), _('week'), _('y'), _('year'), _('all'), _('alltime')]
        for arg in args:
            arg = arg.lstrip('-')
            if arg in periods:
                period = get_period(arg)
            elif arg != 'm':
                username = arg.lstrip('@')

    user_info = (
        user_info_from_message_or_reply(message)
        if username is None
        else user_info_from_username(db, username)
    )

    if user_info is None:
        message.reply_text(_(f'Could not find user named {username}'))
        return

    user_karma = format_number(
        analytics.get_karma(user_info.user_id, message.chat_id, period), locale=LOCALE
    )

    period_suffix = (
        _(f'(since {format_date(period, locale=LOCALE)})')
        if period is not None
        else _(f'(all time)')
    )
    message.reply_text(
        _(f'{user_info.username} has {user_karma} karma in this chat {period_suffix}.')
    )


def karmas(bot: Bot, update: Update):
    """Shows the top 10 karmas in a given group.

    If the group doesn't have at least 10 users, shows as many as there are in
    the group.

    Args:
        bot: The object that represents the Telegram Bot.
        update: The object that represents an incoming update for the bot to handle.
    """
    text = update.message.text
    something, *args = text.split()
    arg = args[0] if args else 'm'
    requested_period = arg.lstrip('-')
    periods = [
        _('m'),
        _('month'),
        _('w'),
        _('week'),
        _('y'),
        _('year'),
        _('all'),
        _('alltime'),
    ]
    if requested_period not in periods:
        update.message.reply_text(_(f'Period {requested_period} is not supported.'))
        return

    period = get_period(arg)

    top_users = analytics.get_top_n_karmas(update.message.chat.id, 10, period)

    response = '\n'.join(
        f'{i} - {user.name} ({format_number(user.karma, locale=LOCALE)})'
        for i, user in enumerate(top_users, 1)
    )

    update.message.reply_text(response)


def devil(bot: Bot, update: Update):
    """Reply the user with some dumb text and the person with the lowest karma, the "devil".

    Args:
        bot: The object that represents the Telegram Bot.
        update: The object that represents an incoming update for the bot to handle.
    """
    group_devil = analytics.get_devil_saint(update.message.chat.id).devil
    response = _(
        f"{group_devil.name}, there's a special place in hell for you, see you there."
    )

    update.message.reply_text(response)


def saint(bot: Bot, update: Update):
    """Reply the user with a message and the person with the highest karma, the "saint".

    Args:
        bot: The object that represents the Telegram Bot.
        update: The object that represents an incoming update for the bot to handle.
    """
    group_saint = analytics.get_devil_saint(update.message.chat.id).saint
    response = _(
        f"{group_saint.name}, apparently you're the nicest person here. I don't like you."
    )

    update.message.reply_text(response)


HANDLERS = [
    CommandHandler('average_length', average_length),
    CommandHandler('karma', karma),
    CommandHandler('karmas', karmas),
    CommandHandler('devil', devil),
    CommandHandler('saint', saint),
]
