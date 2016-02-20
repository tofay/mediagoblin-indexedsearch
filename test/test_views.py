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


def test_search_view(test_app):
        # Collection option should have been removed if the user has no
        # collections.
        response = test_app.get('/search/')

        # Form should only have a submit field and a search field.
        # assert len(response.form.fields) == 2 <- not correct with form in
        # header
        # assert 'query' in response.form.fields

        # TODO: add media with images and check that the query form returns
        # them in searches. Or just query the index directly...?
        """
        user1 = fixture_add_user()
        user2 = fixture_add_user(username=u'different')

        media_a = fixture_media_entry(title=u'some photo', uploader=user1.id,
                                      save=False, expunge=False,
                                      fake_upload=False)
        media_b = fixture_media_entry(title=u'mediaB', uploader=user2.id,
                                      save=False, expunge=False,
                                      fake_upload=False)
        media_c = fixture_media_entry(title=u'mediaC', save=False,
                                      expunge=False, fake_upload=False,
                                      uploader=user1.id)
        media_a.description = u'media description'
        media_b.description = u'DescriptionB'
        media_c.description = u'DescriptionC'
        Session.add(media_a)
        Session.add(media_b)
        Session.add(media_c)
        Session.commit()
                """
