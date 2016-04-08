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
from indexedsearch.backends.whoosh import Engine, INDEX_NAME
import whoosh.index
import whoosh.qparser
import whoosh.writing
from mediagoblin.tools import pluginapi
from mediagoblin.db.base import Session
from mediagoblin.tests.tools import (fixture_media_entry)


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
    engine2 = Engine(**config)
    with engine2.index.searcher() as searcher:
        qp = whoosh.qparser.QueryParser('title', schema=engine2.index.schema)
        query = qp.parse('Test media entry')
        assert len(searcher.search(query)) == 1
