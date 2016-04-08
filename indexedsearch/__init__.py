# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011, 2012 MediaGoblin contributors.  See AUTHORS.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import os
import logging
import importlib

from sqlalchemy import event

from mediagoblin.db.models import MediaEntry, Comment
from mediagoblin.tools import pluginapi

_log = logging.getLogger(__name__)
PLUGIN_DIR = os.path.dirname(__file__)


def setup_plugin(mediagoblin_app):
    _log.info('Setting up search plugin')
    config = pluginapi.get_config('indexedsearch')
    engine = get_engine()
    engine.update_index()

    if config.get('USERS_ONLY'):
        view = 'user_search_results_view'
    else:
        view = 'search_resuls_view'

    routes = [
        ('indexedsearch',
         '/search/',
         'indexedsearch.views:' + view)]

    pluginapi.register_routes(routes)
    pluginapi.register_template_path(os.path.join(PLUGIN_DIR, 'templates'))

    search_link_style = config.get('SEARCH_LINK_STYLE')
    _log.debug("Search link style was specified as: %r", search_link_style)

    if search_link_style in ['button', 'link', 'none', 'form']:
        header_template = ('indexedsearch/search_link_%s.html' %
                           search_link_style)
    else:
        header_template = 'indexedsearch/search_link_form.html'

    pluginapi.register_template_hooks(
        {'header_extra': header_template})

    add_event_hooks()
    return mediagoblin_app


hooks = {
    'wrap_wsgi': setup_plugin
}


def get_engine():
    config = pluginapi.get_config('indexedsearch')
    backend_module = importlib.import_module(config.get('BACKEND'))
    return backend_module.Engine(**config)


def comment_change(mapper, connection, comment):
    """If a comment on a media entry has been removed, reindex the entry."""
    if isinstance(comment.target(), MediaEntry):
        get_engine().add_media_entry(comment.target())


def media_entry_updated(mapper, connection, media_entry):
    """If a comment on a media entry has been removed, reindex the entry."""
    get_engine().add_media_entry(media_entry)


def media_entry_deleted(mapper, connection, media_entry):
    """Delete a media entry"""
    get_engine().remove_media_entry(media_entry.id)


def add_event_hooks():
    for event_type in 'after_delete', 'after_update', 'after_insert':
        event.listen(Comment, event_type, comment_change)

    event.listen(MediaEntry, 'after_delete', media_entry_deleted)
    event.listen(MediaEntry, 'after_update', media_entry_updated)
    event.listen(MediaEntry, 'after_insert', media_entry_updated)
