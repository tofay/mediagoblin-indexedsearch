# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2013 MediaGoblin contributors.  See AUTHORS.
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

import pytest
import pkg_resources
from mediagoblin.tests import tools


@pytest.fixture()
def test_app(request):
    try:
        config_file = request.cls.config_file
    except AttributeError:
        config_file = 'indexedsearch_mediagoblin.ini'

    return tools.get_app(
        request,
        mgoblin_config=pkg_resources.resource_filename(
            'test', config_file))
