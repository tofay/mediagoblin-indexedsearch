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
import datetime
import whoosh.index
import whoosh.qparser
import whoosh.writing
from mediagoblin.tools import pluginapi
from mediagoblin.db.base import Session
from mediagoblin.tests.tools import (fixture_media_entry)
from indexedsearch.backends.whoosh import Engine, INDEX_NAME
from indexedsearch import get_engine


def test_index_creation():
    """
    Test that:
    - an index is created when a first whoosh engine is constructed
    - subsequent engines use the same index.
    """
    dirname = 'test_index'
    config = {'INDEX_DIR': dirname}
    engine = Engine(**config)

    # Check that an index has been created
    assert os.path.exists(dirname)
    assert whoosh.index.exists_in(dirname, INDEX_NAME)

    # Add an entry to the engine's index.
    with whoosh.writing.AsyncWriter(engine.index) as writer:
        doc = {'media_id': 1,
               'title': 'Test media entry'}
        writer.update_document(**doc)

    # Now open a new engine and check that the entry we just added is in the
    # new engine's index.
    assert Engine(**config).search('Test media entry') == [1]


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
    media_a = fixture_media_entry(title='mediaA', save=False,
                                  expunge=False, fake_upload=False,
                                  state='processed')
    media_b = fixture_media_entry(title='mediaB', save=False,
                                  expunge=False, fake_upload=False,
                                  state='processed')
    media_c = fixture_media_entry(title='mediaC', save=False,
                                  expunge=False, fake_upload=False,
                                  state='processed')
    media_a.description = 'DescriptionA'
    media_b.description = 'DescriptionB'
    media_c.description = 'DescriptionC'
    Session.add(media_a)
    Session.add(media_b)
    Session.add(media_c)
    Session.commit()

    ix = whoosh.index.open_dir(dirname, indexname=INDEX_NAME)
    with whoosh.writing.AsyncWriter(ix) as writer:
        # Mess up the index by:
        # - changing the time of media_a to a fake time before it was created
        # and changing the description
        # - changing the description of media_b
        # - adding a fake entry
        # - deleting an entry
        writer.update_document(title='{0}'.format(media_a.title),
                               description='fake_description_a',
                               media_id=media_a.id,
                               time=fake_time)

        writer.update_document(title='{0}'.format(media_b.title),
                               description='fake_description_b',
                               media_id=media_b.id,
                               time=media_b.updated)

        writer.update_document(title='fake document',
                               description='fake_description_d',
                               media_id=29,
                               time=fake_time)
        writer.delete_by_term('media_id', media_c.id)

    engine = get_engine()
    engine.update_index()

    with engine.index.searcher() as searcher:
        # We changed the time in the index for media_a, so it should have
        # been audited.
        qp = whoosh.qparser.QueryParser('description',
                                        schema=engine.index.schema)
        query = qp.parse('fake_description_a')
        assert len(searcher.search(query)) == 0
        query = qp.parse('DescriptionA')
        fields = searcher.search(query)[0]
        assert fields['media_id'] == media_a.id

        # media_b shouldn't have been audited, because we didn't change the
        # time, so should still have a fake description.
        query = qp.parse('fake_description_b')
        fields = searcher.search(query)[0]
        assert fields['media_id'] == media_b.id

        # media_c should have been re-added to the index
        query = qp.parse('DescriptionC')
        fields = searcher.search(query)[0]
        assert fields['media_id'] == media_c.id

        # The fake entry, media_d, should have been deleted
        query = qp.parse('fake_description_d')
        assert len(searcher.search(query)) == 0


def test_media_entry_change_and_delete(test_app):
    """
    Test that media entry additions/modification/deletes automatically show
    up in the index.

    """
    media_a = fixture_media_entry(title='mediaA', save=False,
                                  expunge=False, fake_upload=False,
                                  state='processed')
    media_b = fixture_media_entry(title='mediaB', save=False,
                                  expunge=False, fake_upload=False,
                                  state='processed')
    media_a.description = 'DescriptionA'
    media_b.description = 'DescriptionB'
    Session.add(media_a)
    Session.add(media_b)
    Session.commit()

    # Check that the media entries are in the index
    engine = get_engine()
    assert engine.search('mediaA') == [media_a.id]
    assert engine.search('mediaB') == [media_b.id]

    # Modify one, and delete the other
    media_a.title = 'new'
    media_b.delete()

    # Check that the changes are present in the index
    assert engine.search('new') == [media_a.id]
    assert engine.search('mediaA') == []
    assert engine.search('mediaB') == []


def test_unprocess_media_entry(test_app):
    """
    Test that media entries that aren't marked as processed are not added to
    the index.

    """
    dirname = pluginapi.get_config('indexedsearch').get('INDEX_DIR')

    media_a = fixture_media_entry(title='mediaA', save=False,
                                  expunge=False, fake_upload=False,
                                  state='unprocessed')
    media_a.description = 'DescriptionA'
    Session.add(media_a)
    Session.commit()

    # Check that the media entry is not in the index
    ix = whoosh.index.open_dir(dirname, indexname=INDEX_NAME)
    with ix.searcher() as searcher:
        qp = whoosh.qparser.QueryParser('title', schema=ix.schema)
        query = qp.parse('mediaA')
        assert len(searcher.search(query)) == 0
