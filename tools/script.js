function init_graph(data) {
	var container = document.getElementById("graph");

	var parsed = {
	  nodes: new vis.DataSet(data.nodes),
	  edges: new vis.DataSet(data.edges)
	};

	var options = {
	  layout: {
			improvedLayout: false
		},
		nodes: {
			color: {
				border: "rgba(43,124,233,0)",
				background: "rgba(255,255,255,0.70)",
				highlight: {
					border: "#EEE",
					background: "rgba(255,255,255, 0.95)"
				}
			},
			font: {
				size: 20,
				face: "Helvetica"
			},
			shape: "box",
		},
	  edges: {
			"arrows": {
				"middle": {
					"enabled": true,
					"scaleFactor": 1.5
				}
			},
			"smooth": {
				"type": "curvedCW",
				"roundness": 0.35
			},
			hidden: false,
			"color": {
				"highlight": "rgb(42, 216, 99)",
				"inherit": false
			}
		},
		"physics": {
			"forceAtlas2Based": {
				"gravitationalConstant": -600,
				"springLength": 295,
				"springConstant": 0.035,
				"damping": 0.75
			},
			"minVelocity": 0.75,
			"solver": "forceAtlas2Based",
			"timestep": 0.61
		},
		configure: {
			enabled: true,
			filter: 'nodes',
			showButton: true
		}
	}

	// initialize your network!
	var network = new vis.Network(container, parsed, options);
}
