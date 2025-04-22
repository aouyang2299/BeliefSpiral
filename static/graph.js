(function(){
  
    // grab the data you embedded into the page
    const { query, results, all_queries } = window.BELIEF_DATA;
    const form  = document.querySelector('form');
    const input = form.querySelector('input[name="query"]');
  
    // early exit if no data
    if (!Array.isArray(results) || results.length !== 5) {
      document.getElementById('graphSvg').outerHTML =
        '<div class="no-results">' +
        '<p>No results found. Enter a new belief and hit "Search".</p>' +
        '</div>';
      return;
    }

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
  
    const clickListEl = document.getElementById('click-list');
    let clickHistory = JSON.parse(localStorage.getItem('clickHistory') || '[]');

    clickHistory.forEach(text => {
      const li = document.createElement('li');
      li.textContent = text;
      clickListEl.appendChild(li);
    });

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
  
    form.addEventListener('submit', () => {
      // 1) Clear in‑memory and persisted log
      clickHistory = [];
      localStorage.removeItem('clickHistory');
      // 2) Clear the sidebar (optional, since page is reloading)
      clickListEl.innerHTML = '';
      // 3) Let the form continue to submit and do a full page reload
      const belief = input.value.trim();
      if (belief) {
        clickHistory.push(belief);
        localStorage.setItem('clickHistory', JSON.stringify(clickHistory));
    
        const li = document.createElement('li');
        li.textContent = belief;
        clickListEl.appendChild(li);
      }
    });


    document.addEventListener("DOMContentLoaded", () => {
      const randomBtn = document.getElementById("random-btn");
      const input = document.querySelector('input[name="query"]');
      const form = document.querySelector("form");
    
      // Make sure the data exists
      const allQueries = window.BELIEF_DATA?.all_queries || [];
      console.log(`🔢 Total Queries: ${allQueries.length}`);

    
      randomBtn.addEventListener("click", () => {
        if (!allQueries.length) {
          alert("⚠️ No available queries to choose from.");
          return;
        }
  
        const randomIndex = Math.floor(Math.random() * allQueries.length);
        const randomQuery = allQueries[randomIndex];
    
        // Show it in the input
        input.value = randomQuery;
    
        // Submit the form (will reload the page unless you're intercepting it)
        form.submit();
    
      });
    });
  })();