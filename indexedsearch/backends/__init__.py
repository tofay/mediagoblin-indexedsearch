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

import logging

_log = logging.getLogger(__name__)


class MediaNotProcessedError(Exception):
    """Error indicating that a media entry is not marked as processed."""
    pass


class BaseEngine(object):

    def add_media_entry(self, media):
        raise NotImplementedError

    def remove_media_entry(self, media_entry_id):
        raise NotImplementedError

    def update_index(self):
        """Update the index to make it consistent with the database."""
        raise NotImplementedError

    def get_doc_for_media_entry(self, media):
        """Creates a document suitable for indexing.

        If the media entry is not processed then a MediaNotProcessedError
        will be raised.

        Args:
            media: A MediaEntry for indexing.

        """
        _log.info("Indexing: %d" % media.id)

        if media.state != 'processed':
            _log.info('Ignoring: not yet processed')
            raise MediaNotProcessedError()

        tags = ' '.join([tag['name'] for tag in media.tags])
        comments = '\n'.join([comment.content
                             for comment in media.get_comments()])
        # collections = u','.join([col.title for col in media.collections])
        doc = {'title': media.title,
               'description': media.description,
               'media_id': media.id,
               'time': media.updated,
               'tag': tags,
               'comment': comments}

        if media.get_actor:
            doc['user'] = media.get_actor.username

        return doc
