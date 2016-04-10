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
import pytest
import webtest
from six import itervalues
from mediagoblin.tests.tools import fixture_add_user


class TestSearch:

    @pytest.fixture(autouse=True)
    def setup(self, test_app):
        self.test_app = test_app

        # TODO: Possibly abstract into a decorator like:
        # @as_authenticated_user('chris')
        fixture_add_user(privileges=['active', 'uploader', 'commenter'])

        self.login()

        upload_fields = [('title number one', 'description number one'),
                         ('title number two', 'description number two')]
        upload = webtest.forms.Upload(os.path.join('test', 'image.png'))

        for title, description in upload_fields:
            response = self.test_app.get('/submit/')
            # Test upload of an image when a user has no collections.
            submit_form = self.get_form_from_response(response, '/submit/')
            submit_form['file'] = upload
            submit_form['title'] = title
            submit_form['description'] = description
            submit_form.submit()

    def login(self):
        self.test_app.post(
            '/auth/login/', {
                'username': 'chris',
                'password': 'toast'})
    config_file = 'conf_not_users_only.ini'

    def get_form_from_response(self, response, form_action):
        return [form for form in itervalues(response.forms)
                if form.action == form_action][0]

    def test_search_link_present_for_none_user(self):
        """Test the search form isn't present if search is 'users only'."""
        response = self.test_app.get('/')
        search_form = self.get_form_from_response(response, '/search/')
        search_form['q'] = 'number one'
        response = search_form.submit()
        assert response.status_int == 200
        response.mustcontain('<a href="/u/chris/m/title-number-one/">')
        try:
            response.mustcontain('<a href="/u/chris/m/title-number-two/">')
            self.fail('Image two should not be in response')
        except IndexError:
            pass

        response = self.test_app.get('/')
        search_form = self.get_form_from_response(response, '/search/')
        search_form['q'] = 'number two'
        response = search_form.submit()
        assert response.status_int == 200
        response.mustcontain('<a href="/u/chris/m/title-number-two/">')
        try:
            response.mustcontain('<a href="/u/chris/m/title-number-one/">')
            self.fail('Image one should not be in response')
        except IndexError:
            pass

        response = self.test_app.get('/')
        search_form = self.get_form_from_response(response, '/search/')
        search_form['q'] = 'number'
        response = search_form.submit()
        assert response.status_int == 200
        response.mustcontain('<a href="/u/chris/m/title-number-two/">')
        response.mustcontain('<a href="/u/chris/m/title-number-one/">')
