import os
import logging

import whoosh.index
import whoosh.fields
import whoosh.writing
import whoosh.qparser

from mediagoblin.db.models import MediaEntry
from indexedsearch.backends import BaseEngine, MediaNotProcessedError

_log = logging.getLogger(__name__)
INDEX_NAME = 'media_entries'
DEFAULT_SEARCH_FIELDS = ['title', 'description', 'tag', 'comment']


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
    comment = whoosh.fields.TEXT


class Engine(BaseEngine):

    def __init__(self, **connection_options):
        self.index_dir = connection_options.get('INDEX_DIR')

        try:
            self.index = whoosh.index.open_dir(self.index_dir,
                                               indexname=INDEX_NAME)
        except whoosh.index.EmptyIndexError:
            self.maybe_create_index()

    def update_index(self):
        """ Make an index consistent with the database.

        Removes media entries from the index that aren't in the database.
        Indexes media entries that are in the database but not in the index.
        Re-indexes media entries that have been updated since they were last
        indexed.

        Args:
            dirname: directory containing the index.
        """
        _log.info("Updating index ")

        # The set of all media in the index
        indexed_media = set()
        # The set of all media we need to re-index
        to_index = set()

        with self.index.searcher() as searcher:
            with whoosh.writing.AsyncWriter(self.index) as writer:
                # Loop over the stored fields in the index
                for fields in searcher.all_stored_fields():
                    media_id = fields['media_id']
                    indexed_media.add(media_id)

                    media = MediaEntry.query.filter_by(id=media_id).first()
                    if not media:
                        # This entry has been deleted since it was indexed
                        self.remove_media_entry(media_id, writer)
                    else:
                        # Check if this file was changed since it
                        # was indexed
                        indexed_time = fields['time']
                        last_updated = media.updated
                        if last_updated > indexed_time:
                            # The file has changed, delete it and add it to the
                            # list of files to reindex
                            writer.delete_by_term('media_id', media_id)
                            to_index.add(media_id)

                for media in MediaEntry.query.all():
                    if media.id in to_index or media.id not in indexed_media:
                        # This is either a entry that's changed, or a new entry
                        # that wasn't indexed before. So index it!
                        self.add_media_entry(media, writer)

    def add_media_entry(self, media, writer=None):
        """Adds a media entry to the index using a writer.

        Adds a media entry to the index using a writer. If a writer is given
        then the operation won't be committed to the index.

        Args:
            media: a media entry for indexing.
            writer: a whoosh writer to index the media entry.
        """
        commit = False

        if not writer:
            writer = whoosh.writing.AsyncWriter(self.index)
            commit = True
        try:
            writer.update_document(**self.get_doc_for_media_entry(media))

            if commit:
                writer.commit()

        except MediaNotProcessedError:
            pass

    def maybe_create_index(self):
        """Ensure that a given directory contains the plugin's index.

        If the index doesn't exist in the directory, then it will be created.

        """
        new_index_required = False
        # If the directory doesn't exist, or the index doesn't exist in the
        # directory, then a new index will be made.
        if not os.path.exists(self.index_dir):
            _log.info("Index directory doesn't exist: " + self.index_dir)
            os.mkdir(self.index_dir)
            new_index_required = True
        elif not whoosh.index.exists_in(self.index_dir, INDEX_NAME):
            _log.info("Index doesn't exist in " + self.index_dir)
            new_index_required = True

        if new_index_required:
            _log.info("Creating new index in " + self.index_dir)
            self.index = whoosh.index.create_in(self.index_dir,
                                                schema=MediaEntrySchema(),
                                                indexname=INDEX_NAME)
        else:
            _log.info("Using existing index in " + self.index_dir)
            self.index = whoosh.index.open_dir(self.index_dir,
                                               indexname=INDEX_NAME)

    def remove_media_entry(self, media_entry_id, writer=None):
        """Remove a media entry from the index using a writer.

        Removes a media entry from the index using a writer. If a writer is
        given then the operation won't be committed to the index.

        Args:
            media_entry_id: id of the media entry to be removed.
            writer: a whoosh writer for removing the media entry.
        """
        commit = False

        if not writer:
            writer = whoosh.writing.AsyncWriter(self.index)
            commit = True

        _log.info("Deleting media entry with id: %d" % media_entry_id)
        writer.delete_by_term('media_id', media_entry_id)

        if commit:
            writer.commit()

    def search(self, query):
        with self.index.searcher() as searcher:
            query_string = whoosh.qparser.MultifieldParser(
                DEFAULT_SEARCH_FIELDS, self.index.schema).parse(query)
            results = searcher.search(query_string)
            return [result['media_id'] for result in results]
