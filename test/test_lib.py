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
import datetime
import indexedsearch.lib
import whoosh.index
import whoosh.qparser
import whoosh.writing
from mediagoblin.tools import pluginapi
from mediagoblin.db.models import User, LocalUser, MediaEntry
from mediagoblin.db.base import Session
from mediagoblin.tests.tools import (fixture_add_user, fixture_media_entry,
                                     fixture_add_collection)
from mediagoblin.user_pages.lib import add_media_to_collection


def test_maybe_create_index(test_app):
    """
    Test that the maybe_create_index method:
    - creates an index in a directory if none exists
    - doesn't overwrite that an index when called again.
    """
    dirname = pluginapi.get_config('indexedsearch').get('INDEX_DIR')

    # Check that an index has been created during plugin setup.
    assert os.path.exists(dirname)
    assert whoosh.index.exists_in(dirname, indexedsearch.lib.INDEX_NAME)

    # Add a media entry, call maybe_create_index, and check that it didn't
    # create a new index (by checking that the media entry is in the index).
    fixture_media_entry(title=u'media1')
    assert not indexedsearch.lib.maybe_create_index(dirname)

    ix = whoosh.index.open_dir(dirname, indexname=indexedsearch.lib.INDEX_NAME)

    with ix.searcher() as searcher:
        qp = whoosh.qparser.QueryParser('title', schema=ix.schema)
        query = qp.parse(u'media1')
        assert len(searcher.search(query)) == 1


def test_update_index(test_app):
    """
    Test that the update_index method:
    - updates any media entries whose time in the index is prior to the updated
    attribute of the media entry itself
    - ignores any media_entry whose time in the index matches the updated
    attribute of the media entry itself
    - deletes entries from the index that don't exist in the database.
    - adds entries that are missing from the index
    """
    dirname = pluginapi.get_config('indexedsearch').get('INDEX_DIR')

    fake_time = datetime.datetime.utcnow()
    media_a = fixture_media_entry(title=u'mediaA', save=False,
                                  expunge=False, fake_upload=False)
    media_b = fixture_media_entry(title=u'mediaB', save=False,
                                  expunge=False, fake_upload=False)
    media_c = fixture_media_entry(title=u'mediaC', save=False,
                                  expunge=False, fake_upload=False)
    media_a.description = u'DescriptionA'
    media_b.description = u'DescriptionB'
    media_c.description = u'DescriptionC'
    Session.add(media_a)
    Session.add(media_b)
    Session.add(media_c)
    Session.commit()

    ix = whoosh.index.open_dir(dirname, indexname=indexedsearch.lib.INDEX_NAME)
    with whoosh.writing.AsyncWriter(ix) as writer:
        # Mess up the index by:
        # - changing the time of media_a to a fake time before it was created
        # and changing the description
        # - changing the description of media_b
        # - adding a fake entry
        # - deleting an entry
        writer.update_document(title=u'{0}'.format(media_a.title),
                               description=u'fake_description_a',
                               media_id=media_a.id,
                               time=fake_time)

        writer.update_document(title=u'{0}'.format(media_b.title),
                               description=u'fake_description_b',
                               media_id=media_b.id,
                               time=media_b.updated)

        writer.update_document(title=u'fake document',
                               description=u'fake_description_d',
                               media_id=29,
                               time=fake_time)
        writer.delete_by_term('media_id', media_c.id)

    indexedsearch.lib.update_index(dirname)

    with ix.searcher() as searcher:
        # We changed the time in the index for media_a, so it should have
        # been audited.
        qp = whoosh.qparser.QueryParser('description', schema=ix.schema)
        query = qp.parse(u'fake_description_a')
        assert len(searcher.search(query)) == 0
        query = qp.parse(u'DescriptionA')
        fields = searcher.search(query)[0]
        assert fields['media_id'] == media_a.id

        # media_b shouldn't have been audited, because we didn't change the
        # time, so should still have a fake description.
        query = qp.parse(u'fake_description_b')
        fields = searcher.search(query)[0]
        assert fields['media_id'] == media_b.id

        # media_c should have been re-added to the index
        query = qp.parse(u'DescriptionC')
        fields = searcher.search(query)[0]
        assert fields['media_id'] == media_c.id

        # The fake entry, media_d, should have been deleted
        query = qp.parse(u'fake_description_d')
        assert len(searcher.search(query)) == 0


def test_media_entry_change_and_delete(test_app):
    """
    Test that media entry additions/modification/deletes automatically show
    up in the index.

    """
    dirname = pluginapi.get_config('indexedsearch').get('INDEX_DIR')

    media_a = fixture_media_entry(title=u'mediaA', save=False,
                                  expunge=False, fake_upload=False)
    media_b = fixture_media_entry(title=u'mediaB', save=False,
                                  expunge=False, fake_upload=False)
    media_a.description = u'DescriptionA'
    media_b.description = u'DescriptionB'
    Session.add(media_a)
    Session.add(media_b)
    Session.commit()

    # Check that the media entries are in the index
    ix = whoosh.index.open_dir(dirname, indexname=indexedsearch.lib.INDEX_NAME)
    with ix.searcher() as searcher:
        qp = whoosh.qparser.QueryParser('title', schema=ix.schema)
        query = qp.parse(u'mediaA')
        assert searcher.search(query)[0]['media_id'] == media_a.id
        query = qp.parse(u'mediaB')
        assert searcher.search(query)[0]['media_id'] == media_b.id

    # Modify one, and delete the other
    media_a.title = u'new'
    media_b.delete()

    # Check that the changes are present in the index
    with ix.searcher() as searcher:
        qp = whoosh.qparser.QueryParser('title', schema=ix.schema)
        query = qp.parse(u'new')
        assert searcher.search(query)[0]['media_id'] == media_a.id

        query = qp.parse(u'mediaB')
        assert len(searcher.search(query)) == 0

    col1 = fixture_add_collection(u'collection', user=media_a.get_actor)
    add_media_to_collection(col1, media_a, '')