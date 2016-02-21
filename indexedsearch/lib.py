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
from __future__ import unicode_literals

import os
import logging

import celery

import whoosh.index
import whoosh.fields
import whoosh.writing
from mediagoblin.db.models import MediaEntry
from mediagoblin.tools import pluginapi
from sqlalchemy import event


_log = logging.getLogger(__name__)
INDEX_NAME = 'media_entries'
DEFAULT_SEARCH_FIELDS = ['title', 'description', 'tag']
""" List of the index fields that are searched by default.
"""


class MediaEntrySchema(whoosh.fields.SchemaClass):
    """ Whoosh schema for MediaEntry objects.
    """
    media_id = whoosh.fields.NUMERIC(signed=False, unique=True, stored=True)
    title = whoosh.fields.TEXT
    description = whoosh.fields.TEXT
    tag = whoosh.fields.KEYWORD
    # collection = whoosh.fields.KEYWORD(commas=True)
    time = whoosh.fields.DATETIME(stored=True)
    user = whoosh.fields.TEXT


def index_entry(writer, media):
    """ Stores a media entry in the index.

    Uses the given writer to index the given media entry. Unprocessed media
    entries are ignored.

    Args:
        writer: A writer for the whoosh index.
        media: A MediaEntry for indexing.
    """
    _log.info("Indexing: %d" % media.id)

    if media.state != 'processed':
        _log.info('Ignoring: not yet processed')
        return

    tags = ' '.join([tag['name'] for tag in media.tags])
    # collections = u','.join([col.title for col in media.collections])
    index_fields = {'title': media.title,
                    'description': media.description,
                    'media_id': media.id,
                    'time': media.updated,
                    'tag': tags}

    if media.get_actor:
        index_fields['user'] = media.get_actor.username

    writer.update_document(**index_fields)


@celery.task
def update_index(dirname):
    """ Make an index consistent with the database.

    Removes media entries from the index that aren't in the database.
    Indexes media entries that are in the database but not in the index.
    Re-indexes media entries that have been updated since they were last
    indexed.

    Args:
        dirname: directory containing the index.
    """
    _log.info("Updating existing index in " + dirname)
    ix = whoosh.index.open_dir(dirname, indexname=INDEX_NAME)

    # The set of all media in the index
    indexed_media = set()
    # The set of all media we need to re-index
    to_index = set()

    with ix.searcher() as searcher:
        with whoosh.writing.AsyncWriter(ix) as writer:
            # Loop over the stored fields in the index
            for fields in searcher.all_stored_fields():
                media_id = fields['media_id']
                indexed_media.add(media_id)

                media = MediaEntry.query.filter_by(id=media_id).first()
                if not media:
                    # This entry has been deleted since it was indexed
                    writer.delete_by_term('media_id', media_id)

                else:
                    # Check if this file was changed since it
                    # was indexed
                    indexed_time = fields['time']
                    mtime = media.updated
                    if mtime > indexed_time:
                        # The file has changed, delete it and add it to the
                        # list of files to reindex
                        writer.delete_by_term('media_id', media_id)
                        to_index.add(media_id)

            for media in MediaEntry.query.all():
                if media.id in to_index or media.id not in indexed_media:
                    # This is either a entry that's changed, or a new entry
                    # that wasn't indexed before. So index it!
                    index_entry(writer, media)


def maybe_create_index(dirname):
    """Ensure that a given directory contains the plugin's index.

    If the index doesn't exist in the directory, then it will be created.

    Returns:
        True if a new index was created, otherwise returns False.
    """
    new_index_required = False
    # If the directory doesn't exist, or the index doesn't exist in the
    # directory, then a new index will be made.
    if not os.path.exists(dirname):
        _log.info("Index directory doesn't exist: " + dirname)
        os.mkdir(dirname)
        new_index_required = True
    elif not whoosh.index.exists_in(dirname, INDEX_NAME):
        _log.info("Index doesn't exist in " + dirname)
        new_index_required = True

    if new_index_required:
        _log.info("Creating new index in " + dirname)
        whoosh.index.create_in(dirname, schema=MediaEntrySchema(),
                               indexname=INDEX_NAME)
    return new_index_required


@celery.task
def update_entry(media_entry):
    """ Update the entry in the index.

    (Contents of this method could be in media_entry_change, but have been
    moved here for the future possibility of doing this asynchronously with
    celery)
    """
    config = pluginapi.get_config('indexedsearch')
    dirname = config.get('INDEX_DIR')
    ix = whoosh.index.open_dir(dirname, indexname=INDEX_NAME)
    with whoosh.writing.AsyncWriter(ix) as writer:
        # writer.delete_by_term('id', target_id)
        index_entry(writer, media_entry)


@event.listens_for(MediaEntry, 'after_update')
@event.listens_for(MediaEntry, 'after_insert')
def media_entry_change(mapper, connection, media_entry):
    """ sqlalchemy hook for indexing media entries
    """
    update_entry(media_entry)


@celery.task
def delete_entry(media_entry):
    """ Like update_entry, but for removal
    """
    config = pluginapi.get_config('indexedsearch')
    dirname = config.get('INDEX_DIR')
    ix = whoosh.index.open_dir(dirname, indexname=INDEX_NAME)
    with whoosh.writing.AsyncWriter(ix) as writer:
        _log.info("Unindexing media entry with id: %d" % media_entry.id)
        writer.delete_by_term('media_id', media_entry.id)


@event.listens_for(MediaEntry, 'after_delete')
def media_entry_deleted(mapper, connection, media_entry):
    """ sqlalchemy hook for removing media entries
    """
    delete_entry(media_entry)
