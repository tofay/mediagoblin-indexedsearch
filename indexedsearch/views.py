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
from mediagoblin.db.models import MediaEntry
from mediagoblin.decorators import require_active_login, uses_pagination
from mediagoblin.tools.response import render_to_response
from mediagoblin.tools.pagination import Pagination
from mediagoblin.tools import pluginapi
from mediagoblin.meddleware.csrf import csrf_exempt

from indexedsearch import get_engine
import indexedsearch.forms

import logging
_log = logging.getLogger(__name__)


@require_active_login
def user_search_results_view(request):
    return search_results_view(request)


@csrf_exempt
@uses_pagination
def search_results_view(request, page):
    media_entries = None
    pagination = None
    form = indexedsearch.forms.SearchForm(request.form)

    config = pluginapi.get_config('indexedsearch')
    if config.get('SEARCH_LINK_STYLE') == 'form':
        form.show = False
    else:
        form.show = True

    query = None
    if request.method == 'GET' and 'q' in request.GET:
        query = request.GET['q']

    if query:
        engine = get_engine()
        result_ids = engine.search(query)

        if result_ids:
            matches = MediaEntry.query.filter(
                MediaEntry.id.in_(result_ids))
            pagination = Pagination(page, matches)
            media_entries = pagination()

    return render_to_response(
        request,
        'indexedsearch/results.html',
        {'media_entries': media_entries,
         'pagination': pagination,
         'form': form})
