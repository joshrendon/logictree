document.addEventListener("DOMContentLoaded", () => {
  const select = document.getElementById("view-select");
  const container = document.getElementById("graph-container");

  function fetchAndRender(view) {
    fetch(`/api/tree?view=${view}`)
      .then((response) => response.json())
      .then((data) => {
        console.log("Fetched tree for view:", view, data);
        renderTree(data);
      })
      .catch((error) => {
        console.error("Failed to load tree logic:", error);
      });
  }

  function renderTree(data) {
    if (!container) {
      console.error("Element with id='graph-container' not found.");
      return;
    }

    container.innerHTML = ""; // Clear old tree

    const svg = d3.select(container)
      .append("svg")
      .attr("width", 1000)
      .attr("height", 600);

    const root = d3.hierarchy(data);
    const treeLayout = d3.tree().size([800, 500]);
    treeLayout(root);

    // Draw edges
    svg.selectAll("line")
      .data(root.links())
      .enter()
      .append("line")
      .attr("x1", d => d.source.x + 100)
      .attr("y1", d => d.source.y + 50)
      .attr("x2", d => d.target.x + 100)
      .attr("y2", d => d.target.y + 50)
      .attr("stroke", "#aaa");

    // Draw nodes
    svg.selectAll("circle")
      .data(root.descendants())
      .enter()
      .append("circle")
      .attr("cx", d => d.x + 100)
      .attr("cy", d => d.y + 50)
      .attr("r", 14)
      .attr("fill", "#e0e0e0");

    // Labels
    svg.selectAll("text")
      .data(root.descendants())
      .enter()
      .append("text")
      .attr("x", d => d.x + 100)
      .attr("y", d => d.y + 45)
      .attr("text-anchor", "middle")
      .text(d => d.data.label || "?");
  }

  if (select) {
    select.addEventListener("change", () => {
      fetchAndRender(select.value);
    });
    fetchAndRender(select.value); // Initial load
  } else {
    console.error("Dropdown with id='view-select' not found.");
  }
});




//// static/explorer.js
//window.addEventListener("DOMContentLoaded", () => {
//  const select = document.getElementById("view-select");
//  if (!select) {
//    console.error("Could not find #view-select");
//    return;
//  }
//
//  function fetchAndRender(view) {
//    fetch(`/api/tree?view=${view}`)
//      .then((response) => response.json())
//      .then((data) => {
//        // clear previous render
//        d3.select("#tree-container").selectAll("*").remove();
//        //document.getElementById("tree-container").innerHTML = "";
//        renderTree(data);
//      })
//      .catch((error) => {
//        console.error("Failed to load logic tree:", error);
//      });
//  }
//
//  select.addEventListener("change", () => {
//    fetchAndRender(select.value);
//  });
//
//  // Initial render
//  fetchAndRender(select.value);
//});
//
//document.addEventListener("DOMContentLoaded", function () {
//  const select = document.getElementById("view-select");
//  if (!select) {
//      console.error("Missing #view-select dropdown")
//      return;
//  }
//
//  function fetchAndRender(view) {
//    fetch(`/api/tree?view=${view}`)
//      .then((response) => response.json())
//      .then((data) => {
//        // Clear any previous SVG
//        document.getElementById("tree-container").innerHTML = "";
//        renderTree(data); // assumes `data` is a single root node with children
//      })
//      .catch((error) => {
//        console.error("Failed to load logic tree:", error);
//      });
//  }
//
//  select.addEventListener("change", function () {
//    const selectedView = select.value;
//    console.log("Switching to view", selectedView);
//    fetchAndRender(selectedView);
//  });
//
//  // Initial load
//  fetchAndRender(select.value);
//});
//
//function renderTree(root) {
//  const width = 960;
//  const height = 600;
//
//  const svg = d3
//    .select("#tree-container")
//    .append("svg")
//    .attr("width", width)
//    .attr("height", height)
//    .append("g")
//    .attr("transform", "translate(40,0)");
//
//  const treeLayout = d3.tree().size([height, width - 160]);
//
//  // Use d3.hierarchy to build the tree from your JSON
//  const rootNode = d3.hierarchy(root, (d) => d.children);
//
//  treeLayout(rootNode);
//
//  // Links
//  svg
//    .selectAll(".link")
//    .data(rootNode.links())
//    .enter()
//    .append("path")
//    .attr("class", "link")
//    .attr("fill", "none")
//    .attr("stroke", "#ccc")
//    .attr("d", d3.linkHorizontal().x((d) => d.y).y((d) => d.x));
//
//  // Nodes
//  const node = svg
//    .selectAll(".node")
//    .data(rootNode.descendants())
//    .enter()
//    .append("g")
//    .attr("class", "node")
//    .attr("transform", (d) => `translate(${d.y},${d.x})`);
//
//  node
//    .append("circle")
//    .attr("r", 5)
//    .attr("fill", "#666");
//
//  node
//    .append("text")
//    .attr("dy", 3)
//    .attr("x", (d) => (d.children ? -10 : 10))
//    .style("text-anchor", (d) => (d.children ? "end" : "start"))
//    .text((d) => d.data.label);
//}

//function renderTree(treeData) {
//    const container = document.getElementById("treeContainer");
//    container.innerHTML = "";
//
//    const svg = d3.create("svg")
//        .attr("width", "100%")
//        .attr("height", 600)
//        .style("font", "14px sans-serif");
//
//    const g = svg.append("g")
//        .attr("transform", "translate(40,40)");
//
//    const treeLayout = d3.tree().size([800, 500]);
//
//    const root = d3.hierarchy(treeData, d => d.children);
//    treeLayout(root);
//
//    g.selectAll("link")
//        .data(root.links())
//        .enter()
//        .append("line")
//        .attr("x1", d => d.source.x)
//        .attr("y1", d => d.source.y)
//        .attr("x2", d => d.target.x)
//        .attr("y2", d => d.target.y)
//        .attr("stroke", "#999");
//
//    const node = g.selectAll("node")
//        .data(root.descendants())
//        .enter()
//        .append("g")
//        .attr("transform", d => `translate(${d.x},${d.y})`);
//
//    node.append("circle")
//        .attr("r", 20)
//        .attr("fill", d => d.children ? "#88c" : "#c88");
//
//    node.append("text")
//        .attr("dy", 5)
//        .attr("text-anchor", "middle")
//        .attr("fill", "#fff")
//        .text(d => d.data.label || d.data.type);
//}
//
//function updateView() {
//    const view = document.getElementById("viewSelector").value;
//    fetch(`/api/tree?view=${view}`)
//        .then(response => {
//            if (!response.ok) {
//                throw new Error("Failed to fetch tree");
//            }
//            return response.json();
//        })
//        .then(data =>  {
//            console.log("Fetched tree:", data);
//            renderTree(data);
//        })
//        .catch(err => {
//            console.error(err);
//            alert("Could not load tree view.");
//        });
//}
//
//// Load initial tree on page load
//window.onload = () => {
//    updateView();
//};

//let trees = {};
//let currentTree = "original";
//
//function renderTree(data) {
//  d3.select("#graph").selectAll("*").remove();
//  const width = 960, height = 600;
//  const treeLayout = d3.tree().size([height, width - 160]);
//
//  const root = d3.hierarchy(data);
//  treeLayout(root);
//
//  console.log("Drawing tree:", data.label);
//
//  const svg = d3.select("#graph").append("svg")
//    .attr("width", width)
//    .attr("height", height);
//
//  const g = svg.append("g").attr("transform", "translate(80,0)");
//
//  g.selectAll(".link")
//    .data(root.links())
//    .enter().append("path")
//    .attr("fill", "none")
//    .attr("stroke", "#555")
//    .attr("d", d3.linkHorizontal().x(d => d.y).y(d => d.x));
//
//  const nodes = root.descendants ? root.descendants() : [];
//  console.log("Found", nodes.length, "nodes");
//  const node = g.selectAll(".node")
//    .data(root.descendants())
//    .enter().append("g")
//    .attr("transform", d => `translate(${d.y},${d.x})`);
//
//  node.append("circle")
//    .attr("r", 5)
//    .attr("fill", "#666");
//
//  node.append("text")
//    .attr("dx", 10)
//    .attr("dy", 3)
//    .text(d => formatLabel(d.data));
//}
//
//function formatLabel(d) {
//  if (!d.children || d.children.length === 0) {
//    return d.label; // Leaf: a, b, 1, 0
//  }
//  return d.type || d.label; // Internal node: MUX, XNOR, AND
//}
//
//fetch('/api/tree')
//  .then(response => response.json())
//  .then(data => {
//      console.log("Loaded tree:", data);
//      trees = data;
//      renderTree(trees["simplified"]); // default view
//      //renderTree(data);
//});
//
//document.addEventListener("DOMContentLoaded", () => {
//    const viewSelect = document.getElementById("view-select");
//    if (viewSelect) {
//        viewSelect.addEventListener("change", () => {
//            const selected  = viewSelect.value;
//            console.log("DEBUG: change selected:", selected)
//            if (trees[selected]) {
//                renderTree(trees[selected]);
//            }
//        });
//    }
//});
