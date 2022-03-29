# tiled data server

[***tiled***](https://blueskyproject.io/tiled/) provides a data server
to view acquired data (from databroker catalogs or local files).  

## tiled client

Here, we only provide instructions to *access* an APS tiled server providing
catalog (`bdp2022`) for the BDP data:

In a web browser with access to the APS network, visit
URL: http://wow.xray.aps.anl.gov:8010/ui/browse/bdp2022

Data from each measurement is presented by `uid` in chronolgocial order.  The
most recent is presented at the *end* of the list.  (Yes, the interface is quite
new and not very focused yet on real user activities.)

Click on the uid of interest.  Usually, the data to view is found by proceeding
through this chain: *`uid`* -> *primary* -> *data* -> *adsimdet_image*, such as
this example:
http://wow.xray.aps.anl.gov:8010/ui/browse/bdp2022/bdded59a-3d07-441a-af18-35d72adac12b/primary/data/data_vars/adsimdet_image

The tiled server can provide this same image data via a web socket
request.  See the tiled documentation for details.

## tiled server

Support is provided to start a tiled data server process but the documentation
is scant.  The software requires a special conda environment with development
versions of several libraries.  Use the `create_env.sh` bash shell script to
setup that conda environment.

The databroker catalogs are described in `./tiled/config.yml`

Start the bluesky queueserver (in a background screen session):

```bash
cd ./tiled
./tiled_server.sh start
```
