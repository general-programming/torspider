function init_graph(data) {
	var container = document.getElementById("graph");

	var parsed = {
	  nodes: new vis.DataSet(data.nodes),
	  edges: new vis.DataSet(data.edges)
	};

	var options = {
	  layout: {

	  },
	  edges: {
	    smooth: false,
			hidden: false
	  },
	  physics: {
	    repulsion: {
	      centralGravity: 0.02,
	      springLength: 500,
	      nodeDistance: 750
	    },
	    minVelocity: 0.75,
	    solver: "repulsion",
	    timestep: 0.15
	  }
	}

	// initialize your network!
	var network = new vis.Network(container, parsed, options);

	// network.on("doubleClick", function (params) {
	//   var node = parsed.nodes.get(params["nodes"][0]);
	//   var url = node.label;
	//   window.open("http://" + url + ".tumblr.com");
	// });
}