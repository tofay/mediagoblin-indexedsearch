=======================
mediagoblin-indexedsearch
=======================

This plugin is an adaptation of the excellent mediagoblin-basicsearch plugin (https://github.com/ayleph/mediagoblin-basicsearch/) to support more complex queries.

It adds support for searching media in Gnu MediaGoblin. In its current state, the search function will query the tags, title and description fields of processed media entries for the given input phrase (case-insensitive).

More complex queries are supported, e.g searching for media with tagged with "hello" and not tagged with "goodbye" (the query for this would be "tags:hello -tags:goodbye"). See http://whoosh.readthedocs.org/en/latest/querylang.html for more syntax info.

NB: This relies on a hook not present in any version mediagoblin. Details later.

Set up the search plugin
========================

1. Clone the search plugin repository from GitHub. ::

    $ git clone https://github.com/tofay/mediagoblin-indexedsearch.git

2. Copy the indexedsearch folder to your MediaGoblin plugin path. ::

    $ cp -r mediagoblin-indexedsearch/indexedsearch /path/to/mediagoblin/mediagoblin/plugins/

3. Enable the mediagoblin-indexedsearch plugin by adding the following line to the ``[plugins]`` section of your mediagoblin_local.ini file. ::

    [[mediagoblin.plugins.indexedsearch]]

4. Restart your MediaGoblin instance for the config file changes to be effective.

Configure the search plugin
===========================

The search plugin adds a search link to the top header bar of the MediaGoblin instance. You may specify the display style of the search link in your mediagoblin config file. There are three options for the search link display style.

* ``link`` displays a normal text link next to the Log In link. This is the default display style.
* ``button`` displays an action button link next to the Log In link.
* ``none`` does not display a link. This is useful if you want to create your own search link in a user_dev template or custom theme.

If you choose to specify the display style, add it to your mediagoblin_local.ini like this. ::

    [[mediagoblin.plugins.indexedsearch]]
    SEARCH_LINK_STYLE = 'link'

If you choose style ``none`` and wish to create your own search link, use the syntax below as a guide. ::

    <a href="{{ request.urlgen('mediagoblin.plugins.indexedsearch') }}">
    {%- trans %}Search{% endtrans -%}
    </a>
