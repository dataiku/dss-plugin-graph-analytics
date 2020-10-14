let webAppDesc = dataiku.getWebAppDesc()['chart']
var webAppConfig;
var filters;
var config;

var network;
var allNodes;
var highlightActive = false;
var nodesDataset;
var edgesDataset;

function stopStabilization(network, time){
    setTimeout(() => {
            network.stopSimulation();
            console.log("Stabilization stopped !")
        },
        time
    );
}

function draw(nodes, edges, options, time) {
    var container = document.getElementById('graph-chart');
    var data = {
        nodes: nodes,
        edges: edges
    };
    return new vis.Network(container, data, options);
}

window.parent.postMessage("sendConfig", "*");

window.addEventListener('message', function(event) {
    if (event.data) {

        event_data = JSON.parse(event.data);
        var same_filters = isEqual(filters, event_data['filters'])
        var same_webappconfig = isEqual(webAppConfig, event_data['webAppConfig'])

        if (same_webappconfig && same_filters) {
            return;
        } else if (same_webappconfig) {
            filters = event_data['filters']
        } else {
            webAppConfig = event_data['webAppConfig']
            filters = event_data['filters']
        
            // catch when filter all alphanum column type values
            try {
                checkWebAppParameters(webAppConfig, webAppDesc);
            } catch (e) {
                dataiku.webappMessages.displayFatalError(e.message);
                return;
            }

            try {
                checkWebAppConfig(webAppConfig)
            } catch (e) {
                dataiku.webappMessages.displayFatalError(e.message);
                return;
            }
        
            var new_config = {
                dataset_name: webAppConfig['dataset'],
                source: webAppConfig['source'],
                target: webAppConfig['target'],
                max_nodes: webAppConfig['max_nodes'],
                directed_edges: webAppConfig['directed_edges']
            }
            if (webAppConfig['advanced_parameters']) {
                var advanced_properties = [
                    "source_nodes_color", "source_nodes_size", "target_nodes_color", "target_nodes_size",
                    "edges_caption", "edges_width", "numerical_colors"
                ]
                for (var i = 0; i < advanced_properties.length; i++) {
                    if (webAppConfig[advanced_properties[i]]) {
                        new_config[advanced_properties[i]] = webAppConfig[advanced_properties[i]]
                    }
                }
            }

            if (isEqual(new_config, config) && same_filters) {
                return;
            }
            config = new_config
        }

        document.getElementById("graph-chart").innerHTML = ""
        document.getElementById("graph-stats").innerHTML = ""
        document.getElementById("spinner").style.display = "block"

        var chart_height = document.body.getBoundingClientRect().height;
        var chart_width = document.body.getBoundingClientRect().width;
        var scale_ratio = Math.max(Math.min(chart_width/chart_height, 2), 0.5)

        dataiku.webappBackend.get('get_graph_data', {"config": JSON.stringify(config), "filters": JSON.stringify(filters), "scale_ratio": scale_ratio})
            .then(
                function(data){
                    nodesDataset = new vis.DataSet(data['nodes']);
                    edgesDataset = new vis.DataSet(data['edges']);
                    var groups = data['groups'];

                    var options = {
                        groups: groups,
                        nodes: {
                            shape: "dot",
                            size: 20,
                            scaling: {
                                min: 10,
                                max: 50                            },
                            font: {
                                size: 12,
                                face: "Tahoma",
                                strokeWidth: 7
                            }
                        },
                        
                        edges:{
                            width: 1,
                            scaling: {
                                min: 1,
                                max: 10,
                                label: false,
                                customScalingFunction: quadraticScalingFunction
                            },
                            color: { inherit: true },
                            smooth: {
                                type: "continuous"
                            },
                            arrows: {
								to: {enabled: config.directed_edges}
							},
                        },
                        interaction: {
                            hideEdgesOnDrag: false,
                            hideEdgesOnZoom: true,
                            tooltipDelay: 200,
                            hoverConnectedEdges: true,
                            navigationButtons: true,
                            keyboard: {
                                enabled: true
                            }
                        },
                        layout: {
                            improvedLayout: true,
                            hierarchical: {
								enabled: false,
								sortMethod: 'hubsize'
							}
						},

                        physics: false
                    };
                    document.getElementById("spinner").style.display = "none";
                    network = draw(nodesDataset, edgesDataset, options, 3000);

                    document.getElementById("graph-stats").innerHTML = `${nodesDataset.length} nodes<br>${edgesDataset.length} edges`

                    allNodes = nodesDataset.get({ returnType: "Object" });

                    network.on("doubleClick", neighbourhoodHighlight);
                }
            ).catch(error => {
                console.warn("just catched an error")
                document.getElementById("spinner").style.display = "none";
                dataiku.webappMessages.displayFatalError(error);
            });
    }
});


function neighbourhoodHighlight(params) {

    console.log("just double clicked on: ", params)
    if (params.nodes.length > 0) {
      highlightActive = true;
      var i, j;
      var selectedNode = params.nodes[0];
      var degrees = 2;
  
      // mark all nodes as hard to read.
      for (var nodeId in allNodes) {
        allNodes[nodeId].color = "rgba(200,200,200,0.5)";
      }
      var connectedNodes = network.getConnectedNodes(selectedNode);
      var allConnectedNodes = [];
  
      // get the second degree nodes
      for (i = 1; i < degrees; i++) {
        for (j = 0; j < connectedNodes.length; j++) {
          allConnectedNodes = allConnectedNodes.concat(
            network.getConnectedNodes(connectedNodes[j])
          );
        }
      }
  
      // all second degree nodes get a different color and their label back
      for (i = 0; i < allConnectedNodes.length; i++) {
        allNodes[allConnectedNodes[i]].color = "rgba(150,150,150,0.75)";
      }
  
      // all first degree nodes get their own color and their label back
      for (i = 0; i < connectedNodes.length; i++) {
        allNodes[connectedNodes[i]].color = undefined;
      }
  
      // the main node gets its own color and its label back.
      allNodes[selectedNode].color = undefined;
    } else if (highlightActive === true) {
      // reset all nodes
      for (var nodeId in allNodes) {
        allNodes[nodeId].color = undefined;
      }
      highlightActive = false;
    }
  
    // transform the object into an array
    var updateArray = [];
    for (nodeId in allNodes) {
      if (allNodes.hasOwnProperty(nodeId)) {
        updateArray.push(allNodes[nodeId]);
      }
    }
    nodesDataset.update(updateArray);
  }