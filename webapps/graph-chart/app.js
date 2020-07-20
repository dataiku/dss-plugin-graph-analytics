let allRows;
let webAppConfig = dataiku.getWebAppConfig()['webAppConfig'];
let webAppDesc = dataiku.getWebAppDesc()['chart']


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
    var network = new vis.Network(container, data, options);
    console.log("Stabilizing ...")
    stopStabilization(network, time);
    
}
console.warn("hello Chart")
window.parent.postMessage("sendConfig", "*");

window.addEventListener('message', function(event) {
    if (event.data) {

        event_data = JSON.parse(event.data);

        console.warn("event_data: ", event_data)

        webAppConfig = event_data['webAppConfig']
        filters = event_data['filters']

        // TODO catch when filter all alphanum column type values
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
        
        var config = {
            dataset_name: webAppConfig['dataset'],
            source: webAppConfig['source'],
            target: webAppConfig['target'],
            max_nodes: webAppConfig['max_nodes'],
            source_nodes_color: webAppConfig['source_nodes_color'],
            source_nodes_size: webAppConfig['source_nodes_size'],
            target_nodes_color: webAppConfig['target_nodes_color'],
            target_nodes_size: webAppConfig['target_nodes_size'],
            edges_caption: webAppConfig['edges_caption'],
            edges_width: webAppConfig['edges_width'],
            directed_edges: webAppConfig['directed_edges']
        }
        // var directed_edges = webAppConfig['directed_edges']

        dataiku.webappBackend.get('get_graph_data', {"config": JSON.stringify(config), "filters": JSON.stringify(filters)})
            .then(
                function(data){

                    var nodes = data['nodes'];
                    var edges = data['edges'];
                    var groups = data['groups']
                    
                    console.log("nodes: ", nodes)
                    console.log("edges: ", edges)
                    console.log("groups: ", groups)

                    var options = {
                        groups: groups,
                        nodes: {
                            shape: "dot",
                            size: 20,
                            scaling: {
                                min: 10,
                                max: 30
                            },
                            font: {
                                size: 12,
                                face: "Tahoma",
                                strokeWidth: 7
                            }
                        },
                        
                        edges:{
                            scaling: {
                                min: 1,
                                max: 5,
                                label: false
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
                            hideEdgesOnDrag: true,
                            hideEdgesOnZoom: true,
                            tooltipDelay: 200,
                            hoverConnectedEdges: true,
                            navigationButtons: true,
                            keyboard: {
                                enabled: true
                            }
                        },
                        layout: {
                            improvedLayout: false,
                            hierarchical: {
								enabled: false,
								sortMethod: 'hubsize'
							}
						},

                        // physics: {
                        //     forceAtlas2Based: {
                        //         gravitationalConstant: -26,
                        //         centralGravity: 0.005,
                        //         springLength: 230,
                        //         springConstant: 0.18
                        //     },
                        //     maxVelocity: 50,
                        //     solver: 'forceAtlas2Based',
                        //     timestep: 0.35,
                        //     stabilization: {
                        //         iterations: 200,
                        //         fit: true
                        //     }
                        // }
                        physics: false
                    };
                    $('#graph-chart').html('');
                    var network = draw(nodes, edges, options, 5000);
                }
            ).catch(error => {
                dataiku.webappMessages.displayFatalError(error);
            });
    }
});
