from django.conf.urls.defaults import *

urlpatterns = patterns('',
    # Example:
    # (r'^frontend/', include('frontend.apps.foo.urls.foo')),

    # Uncomment this for admin:
    (r'^admin/', include('django.contrib.admin.urls')),
)
