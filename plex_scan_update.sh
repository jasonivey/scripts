#!/usr/bin/env bash
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120

# Show the list of sections of libraries and ID's within the Plex server
# curl http://localhost:32400/library/sections?X-Plex-Token=sjB4XnBypwpyBkKzstT2 | xmllint --format -

# To retrieve the plex token enter the Plex Web App and view any item.  Go into the details
#  click on "..." or the more options down box and click on "Get Info".  Then click on the link
#  for "View XML".  This will open a new browser window with some XML.  In the URL one of the
#  arguments will be the "X-Plex-Token=base64-encoded-string".  This can be used for various
#  curl commands.

sudo su -s /bin/bash --command 'LD_LIBRARY_PATH=/usr/lib/plexmediaserver /usr/lib/plexmediaserver/Plex\ Media\ Scanner --verbose --progress --scan --refresh --section 1 --directory "/mnt/seagate/movies/" --no-thumbs' plex
sudo su -s /bin/bash --command 'LD_LIBRARY_PATH=/usr/lib/plexmediaserver /usr/lib/plexmediaserver/Plex\ Media\ Scanner --verbose --progress --scan --refresh --section 2 --directory "/mnt/seagate/television/" --no-thumbs' plex

