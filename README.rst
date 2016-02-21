Search plugin for GNU Mediagoblin
###############

|license_badge| |pypi_badge| |version_badge|
|travis_badge| |status_badge|

.. |license_badge| image:: https://img.shields.io/pypi/l/mediagoblin-indexedsearch.svg
   :target: https://en.wikipedia.org/wiki/Affero_General_Public_License

.. |pypi_badge| image:: https://img.shields.io/pypi/v/mediagoblin-indexedsearch.svg
   :target: https://pypi.python.org/pypi/mediagoblin-indexedsearch

.. |version_badge| image:: https://img.shields.io/pypi/pyversions/mediagoblin-indexedsearch.svg
   :target: https://pypi.python.org/pypi/mediagoblin-indexedsearch

.. |status_badge| image:: https://img.shields.io/pypi/status/mediagoblin-indexedsearch.svg
   :target: https://pypi.python.org/pypi/mediagoblin-indexedsearch

.. |travis_badge| image:: https://travis-ci.org/tofay/mediagoblin-indexedsearch.svg?branch=master
   :target: https://travis-ci.org/tofay/mediagoblin-indexedsearch

.. |status_badge| image:: https://img.shields.io/pypi/status/mediagoblin-indexedsearch.svg
   :target: https://pypi.python.org/pypi/mediagoblin-indexedsearch

.. END_BADGES_TAG

N.B Only works with unreleased dev version of mediagoblin (0.9.0)

``mediagoblin-indexedsearch`` is a plugin for GNU Mediagoblin that adds support for searching media.

By default, the search function will query the tags, title and description fields
of media for the given phrase.

More complex queries are supported, e.g searching for media with tagged with "hello"
and not tagged with "goodbye" (tag:hello -tag:goodbye), or searching for any
media added by the user "tom" (user:tom).

(See http://whoosh.readthedocs.org/en/latest/querylang.html for more syntax info.)

This plugin is based on an existing search plugin, https://github.com/ayleph/mediagoblin-basicsearch/,
but uses a search index for queries.

.. END_DESCRIPTION_TAG


Setting up the search plugin
===========================

Enable the plugin by adding the following line to the ``[plugins]`` section of your mediagoblin config file.

[[indexedsearch]]


The following parameters can be specified in the indexedsearch section of your mediagoblin
config file:

SEARCH_LINK_STYLE = 'link'

Specifies the style of the search link that is added to the top header bar of the MediaGoblin instance.
The options for the search link display style are:

* ``form`` displays a search form next to the Log In link. This is the default display style.
* ``link`` displays a normal text link next to the Log In link.
* ``button`` displays an action button link next to the Log In link.
* ``none`` does not display a link. This is useful if you want to create your own search link in a user_dev template or custom theme.

INDEX_DIR = '/path/to/index/directory'

Specifies the directory in which the plugin will create a search index (the plugin will
create the directory if it doesn't exist, assuming correct permissions etc.). By default the index
will be created in /path/to/mediagoblin/user_dev/searchindex.

USERS_ONLY = True

Specifies whether or not searching for content requires being logged-in. Defaults to True.
