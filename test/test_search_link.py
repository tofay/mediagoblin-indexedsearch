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
from six import itervalues
from mediagoblin.tests.tools import fixture_add_user


#def test_search_link_omitted(test_app):
#    """Test the search form isn't present if search is 'users only'."""
#    response = test_app.get('/')
#    assert '/search/' not in [form.action
#                              for form in itervalues(response.forms)]
                                                                                                

def test_search_link_present(test_app):
    """Test the search form is present if search is 'users only', and
    a user is logged in."""
    fixture_add_user(privileges=['active', 'uploader', 'commenter'])
    test_app.post('/auth/login/', {'username': 'chris',
                                   'password': 'toast'})
    response = test_app.get('/')
    assert '/search/' in [form.action for form in itervalues(response.forms)]


class TestNotUsersOnly:

    config_file = 'conf_not_users_only.ini'

    def test_search_link_present_for_none_user(self, test_app):
        """Test the search form isn't present if search is 'users only'."""
        # Sticking a locale in the request's params is a horrible hack to
        # workaround mediagoblin.tools.templates caching of the jinja
        # environment... If this wasn't here then the global_config used by
        # base_search_link would have USERS_ONLY=True.
        # Maybe this test won't pass outside of the UK?!
        response = test_app.get('/', params={'lang': 'en'})
        assert '/search/' in [form.action
                              for form in itervalues(response.forms)]
