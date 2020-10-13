PLUGIN_VERSION=1.0.0
PLUGIN_ID=graph-analytics

all:
	cat plugin.json|json_pp > /dev/null
	rm -rf dist
	mkdir dist
	zip -r dist/dss-plugin-${PLUGIN_ID}-${PLUGIN_VERSION}.zip code-env custom-recipes web-app-templates plugin.json