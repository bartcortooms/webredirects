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

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from django.db.models import signals
from django.dispatch import dispatcher
import settings

def site_get_absolute_url(self):
	return "http://%s" % self.domain

Site._meta.get_field('domain').help_text = "Please include the www. in the domain name"
Site.get_absolute_url = site_get_absolute_url

# Allow plaintext passwords to be entered in the admin interface.
def user_pre_save(sender, instance, signal, *args, **kwargs):
	user = instance
	if not user.password.startswith('sha1$'):
		user.set_password(user.password)

dispatcher.connect(user_pre_save, signal=signals.pre_save, sender=User)

class Redirect(models.Model):
	source_url = models.CharField(maxlength=128, core=True, verbose_name='Source URL', help_text='Full URL, including a leading /')
	target_url = models.CharField(maxlength=128, core=True, verbose_name='Target URL', help_text='Full URL, optionally starting with http://targetdomain for redirects to a different site.')
	site = models.ForeignKey(Site, edit_inline=True)

	class Meta:
		verbose_name_plural = "redirects"

	def __str__(self):
		return "%s -> %s" % (self.source_url, self.target_url)

	def get_absolute_url(self):
		if self.target_url.startswith("http://"):
			return self.target_url
		else:
			return self.site + self.target_url

class SiteAlias(models.Model):
	alias = models.CharField(maxlength=100, core=True, help_text="Please include the www.")
	site = models.ForeignKey(Site, edit_inline=True)

	class Meta:
		verbose_name_plural = "domain aliases"

	def __str__(self):
		return self.alias

	def get_absolute_url(self):
		return "http://%s" % self.alias

# Remove cache entries for redirects from the memcache server(s)
def invalidate_cache_entries(sender, instance, signal, *args, **kwargs):
	if ((settings.MEMCACHED_SERVERS is None) or
	    (len(settings.MEMCACHED_SERVERS) == 0)):
		return

	import cmemcache

	# We don't know which cache entries exist, and instead of making things
	# complicated for ourselves by trying to flush all possible
	# combinations of sites aliases and URL redirects for the site, we just
	# flush all cache entries.  Updates rarely happen, so this isn't a big
	# deal.
	mc = cmemcache.Client(settings.MEMCACHED_SERVERS)
	mc.flush_all()

dispatcher.connect(invalidate_cache_entries, signal=signals.post_save, sender=Site)
dispatcher.connect(invalidate_cache_entries, signal=signals.post_delete, sender=Site)
