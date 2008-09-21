# Copyright 2008 Kumina bv.
#
# This file is part of webredirects.
#
# webredirects is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# webredirects is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with webredirects.  If not, see <http://www.gnu.org/licenses/>.

from mod_python import apache, util
import os, re
import settings

if (settings.MEMCACHED_SERVERS is not None) and (len(settings.MEMCACHED_SERVERS) > 0):
	import memcache
	use_memcache = True
else:
	use_memcache = False

os.environ["DJANGO_SETTINGS_MODULE"] = "webredirects.settings"

from django.contrib.sites.models import Site
from webredirects.redirects.models import SiteAlias, Redirect
from django.core.exceptions import ObjectDoesNotExist

def get_target_uri(hostname, path):
	target_uri = False
	target_domain = hostname

	# Redirect "foo.nl" to "www.foo.nl".
	m = re.compile('^([^.]+\.[^.]+$)').match(target_domain)
	if m:
		target_domain = "www.%s" % m.group(1)
		target_uri = "http://%s%s" % (target_domain, path)

	# Find aliases for domains
	try:
		sitealias = SiteAlias.objects.get(alias = hostname)
		target_domain = sitealias.site.domain
		target_uri = "http://%s%s" % (target_domain, path)
	except ObjectDoesNotExist:
		pass

	# Find redirects for urls
	try:
		site = Site.objects.get(domain = target_domain)
		target_uri = site.redirect_set.get(source_url = path).target_url
		if (target_uri[0] == '/') and (target_domain == hostname):
			# Internal redirect
			target_uri = "%s" % target_uri
		elif target_uri.startswith("http://") or target_uri.startswith("https://"):
			# External redirect
			target_uri = target_uri
	except ObjectDoesNotExist:
		pass

	return target_uri

def headerparserhandler(req):
	target_uri = None

	# Try a cached lookup first.
	if use_memcache:
		mc = memcache.Client(settings.MEMCACHED_SERVERS)
		target_uri = mc.get(req.hostname + req.uri)

	# Do a full lookup if there is no cache entry.
	if target_uri is None:
		target_uri = get_target_uri(req.hostname, req.uri)

	if use_memcache:
		mc.set(req.hostname + req.uri, target_uri)

	if not target_uri:
		return apache.DECLINED
	else:
		req.headers_out['Location'] = target_uri
		req.status = apache.HTTP_MOVED_PERMANENTLY
		return apache.HTTP_MOVED_PERMANENTLY
