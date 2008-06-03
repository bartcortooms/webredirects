webredirects is meant to make it easy for non-sysadmins to add new redirects
and setup site aliases.  It does this by allowing URL redirects and site
aliases to be managed through a web-based application.  It also allows you to
define a 'placeholder' site, for domains which point to your domain but have
not been setup yet.

The webapplication (frontend) for managing the redirects stores the redirects
and aliases in an SQL database.  The backend of webredirects hooks into Apache
with mod_python and rewrites URLs to their new location by looking up the
redirects and site aliases in the SQL database.  It caches the results of the
lookups in memcached to speedup the URL rewrites.

                               -  Bart Cortooms <bart@kumina.nl>, Kumina, 2008
