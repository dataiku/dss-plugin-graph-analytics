let webAppDesc = dataiku.getWebAppDesc()['chart']
var webAppConfig = {};
var filters = {};
var plugin_config = {};

var network;
var allNodes;
var highlightActive = false;
var nodesDataset;
var edgesDataset;

var globalCallbackNum = 0;
var waitingTime;

function sleep (time) {
    return new Promise((resolve) => setTimeout(resolve, time));
}

function draw(nodes, edges, options) {
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
            // some events such as resizing the window should not do anything
            return;
        } else {
            webAppConfig = event_data['webAppConfig']
            filters = event_data['filters']
        
            // catch when filter all alphanum column type values
            try {
                checkWebAppParameters(webAppConfig, webAppDesc);
            } catch (e) {
                plugin_config = {}
                document.getElementById("graph-stats").innerHTML = ""
                dataiku.webappMessages.displayFatalError(e.message);
                return;
            }

            try {
                checkWebAppConfig(webAppConfig)
            } catch (e) {
                plugin_config = {}
                document.getElementById("graph-stats").innerHTML = ""
                dataiku.webappMessages.displayFatalError(e.message);
                return;
            }
        
            var new_plugin_config = {
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
                        new_plugin_config[advanced_properties[i]] = webAppConfig[advanced_properties[i]]
                    }
                }
            }

            if (isEqual(new_plugin_config, plugin_config) && same_filters) {
                // selecting 'Show advanced options' should not do anything if no advanced parameters are selected
                return;
            }
            // waiting for a potential new callback is only neccesary for INT type parameters (too responsive otherwise)
            if (new_plugin_config['max_nodes'] != plugin_config['max_nodes']) {
                waitingTime = 800
            } else {
                waitingTime = 0
            }
            plugin_config = new_plugin_config
        }

        document.getElementById("graph-chart").innerHTML = ""
        document.getElementById("graph-stats").innerHTML = ""
        document.getElementById("spinner").style.display = "block"

        var chart_height = document.body.getBoundingClientRect().height;
        var chart_width = document.body.getBoundingClientRect().width;
        var scale_ratio = Math.max(Math.min(chart_width/chart_height, 2), 0.5)

        globalCallbackNum += 1;
        var thisCallbackNum = globalCallbackNum;
        console.log(`waiting for new callback before calling backend`);
        sleep(waitingTime).then(() => {  // waiting before calling backend that no new callback was called during a small time interval 
            if (thisCallbackNum != globalCallbackNum) {  // another callback incremented globalThreadNum during the time interval
                console.log(`backend not called - overridden by new callback`);
                return;
            } else {        
                console.log(`calling backend`);
                dataiku.webappBackend.post('get_graph_data', {"config": JSON.stringify(plugin_config), "filters": JSON.stringify(filters), "scale_ratio": scale_ratio})
                    .then(
                        function(data){
                            console.log(`backend done`);
                            var nodes = data['nodes']
                            var edges = data['edges']

                            nodes.forEach(function (node) {
                                node.title = htmlTitle(node.title)
                            });

                            edges.forEach(function (edge) {
                                edge.title = htmlTitle(edge.title)
                            });

                            nodesDataset = new vis.DataSet(nodes);
                            edgesDataset = new vis.DataSet(edges);
                            var groups = data['groups'];

                            var options = {
                                groups: groups,
                                nodes: {
                                    shape: "dot",
                                    size: 20,
                                    scaling: {
                                        min: 10,
                                        max: 50                            
                                    },
                                    font: {
                                        size: 20,
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
                                        to: {enabled: plugin_config.directed_edges}
                                    },
                                },
                                interaction: {
                                    hideEdgesOnDrag: false,
                                    hideEdgesOnZoom: true,
                                    tooltipDelay: 200,
                                    hoverConnectedEdges: true,
                                    navigationButtons: false,
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
                            network = draw(nodesDataset, edgesDataset, options);

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