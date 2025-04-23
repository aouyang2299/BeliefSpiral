(function(){
  
    // grab the data you embedded into the page
    const { query, results, all_queries } = window.BELIEF_DATA;
    const form  = document.querySelector('form');
    const input = form.querySelector('input[name="query"]');
    const clickListEl = document.getElementById('click-list');
    let clickHistory = JSON.parse(localStorage.getItem('clickHistory') || '[]');

    function drawGraph(query, results) {
      const svg        = document.getElementById('graphSvg');
      svg.innerHTML    = '<g id="edges"></g><g id="nodes"></g>';
      const edgesLayer = svg.querySelector('#edges');
      const nodesLayer = svg.querySelector('#nodes');
    
      const W = 600, H = 600;
      const cx = W / 2, cy = H / 2;
      const R = 220;
      const startAngle = -Math.PI / 2;
      const padding = 8;
    
      // Helper to create SVG elements
      function make(tag, attrs) {
        const el = document.createElementNS('http://www.w3.org/2000/svg', tag);
        for (let k in attrs) el.setAttribute(k, attrs[k]);
        return el;
      }
      // Helper to add clicks to history
      function logClick(text) {
        // record in memory
        clickHistory.push(text);
        // persist
        localStorage.setItem('clickHistory', JSON.stringify(clickHistory));
        // append to DOM
        const li = document.createElement('li');
        li.textContent = text;
        clickListEl.appendChild(li);
      }
    
      // Draw center node
      const centerText = make('text', { x: cx, y: cy, class: 'label' });
      centerText.textContent = query;
      nodesLayer.appendChild(centerText);
    
      const centerBox = centerText.getBBox();
      const centerRect = make('rect', {
        x: centerBox.x - padding,
        y: centerBox.y - padding,
        width:  centerBox.width  + padding * 2,
        height: centerBox.height + padding * 2,
        class: 'node-box'
      });
      nodesLayer.insertBefore(centerRect, centerText);
    
      // Draw connected outer nodes
      results.forEach((txt, i) => {
        const angle = startAngle + i * (2 * Math.PI / 5);
        const x = cx + R * Math.cos(angle);
        const y = cy + R * Math.sin(angle);
    
        // Edge
        edgesLayer.appendChild(make('line', {
          x1: cx, y1: cy, x2: x, y2: y, class: 'edge'
        }));
    
        // Text
        const nodeText = make('text', { x, y, class: 'label' });
        nodeText.textContent = txt;
        nodesLayer.appendChild(nodeText);
    
        // Box
        const nodeBox = nodeText.getBBox();
        const nodeRect = make('rect', {
          x: nodeBox.x - padding,
          y: nodeBox.y - padding,
          width:  nodeBox.width  + padding * 2,
          height: nodeBox.height + padding * 2,
          class: 'node-box'
        });
        nodesLayer.insertBefore(nodeRect, nodeText);
    
        // Click behavior
        [nodeRect, nodeText].forEach(el =>
          el.addEventListener('click', () => {
            logClick(txt);
            input.value = txt;
            form.submit();
          })
        );
      });
    }
    drawGraph(query, results)

    clickHistory.forEach(text => {
      const li = document.createElement('li');
      li.textContent = text;
      clickListEl.appendChild(li);
    });
  
    //Appends first search to clickHistory
    const isFirstGraph = window.BELIEF_DATA?.results?.length === 5 && clickHistory.length === 0;
    if (isFirstGraph) {
      const firstQuery = window.BELIEF_DATA.query;
    
      clickHistory.push(firstQuery);
      localStorage.setItem("clickHistory", JSON.stringify(clickHistory));
    
      const li = document.createElement("li");
      li.textContent = firstQuery;
      document.getElementById("click-list").appendChild(li);
    }
  
    //CLEARS clickHistory WHEN NEEDED
    function clearHistory() {
      clickHistory = [];
      localStorage.removeItem("clickHistory");
      document.getElementById("click-list").innerHTML = "";
    }
    form.addEventListener('submit', () => {
      clearHistory()
      
    });
    const homeLink = document.getElementById("home-link");
    homeLink?.addEventListener("click", () => {
      clearHistory(); // ✅ clears visual + saved click log before reload
    });

    //RANDOM BUTTON 
    const randomBtn  = document.getElementById("random-btn");
    const allQueries = window.BELIEF_DATA.all_queries;
    
      randomBtn.addEventListener("click", () => {
        console.log("🌀 Random button clicked!");

        clearHistory?.(); // optional chaining if it's not defined yet
    
        const randomQuery = allQueries[
          Math.floor(Math.random() * allQueries.length)
        ];
    
        input.value = randomQuery;
        form.submit();
      });

          // early exit if no data
    if (!Array.isArray(results) || results.length !== 5) {
      document.getElementById('graphSvg').outerHTML =
        '<div class="no-results">' +
        '<p>Enter a new belief and hit "Search".</p>' +
        '</div>';
      return;
    }

    function sendClicksToServer() {
      return fetch('/process_clicks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        // PASS clickHistory
        body: JSON.stringify({ clicked: clickHistory })
      })
      .then(res => {
        if (!res.ok) throw new Error(res.statusText);
        return res.json();
      })
      .then(data => {
        document.getElementById('story').innerText = data.story;
      });
    }
  
    // 3) Wait for DOM load if you haven’t already placed this at the bottom
    document.addEventListener('DOMContentLoaded', () => {
      const btn = document.getElementById('button');
      console.log('Make Story button:', btn);  // should log the <div>
      btn.addEventListener('click', e => {
        e.preventDefault();
        sendClicksToServer().catch(err => {
          console.error(err);
          document.getElementById('story').innerText = '❌ Failed to generate story';
        });
      });
    });

    
  })();