(function(){
  
    // grab the data you embedded into the page
    const { query, results, all_queries } = window.BELIEF_DATA;
    const form  = document.querySelector('form');
    const input = form.querySelector('input[name="query"]');
  
    // helper to make SVG elements
    function make(tag, attrs) {
      const el = document.createElementNS('http://www.w3.org/2000/svg', tag);
      for (let k in attrs) el.setAttribute(k, attrs[k]);
      return el;
    }
  
    // early exit if no data
    if (!Array.isArray(results) || results.length !== 5) {
      document.getElementById('graphSvg').outerHTML =
        '<div class="no-results">' +
        '<p>No results found. Enter a new belief and hit "Search".</p>' +
        '</div>';
      return;
    }
  
    // set up SVG layers
    const svg        = document.getElementById('graphSvg');
    svg.innerHTML    = '<g id="edges"></g><g id="nodes"></g>';
    const edgesLayer = svg.querySelector('#edges');
    const nodesLayer = svg.querySelector('#nodes');

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
  
    // constants
    const W   = 600, H = 600;
    const cx  = W/2, cy = H/2;
    const R   = 220;
    const startAngle = -Math.PI/2;
    const padding    = 8;
  
    // draw center node
    (function drawCenter(){
      const t = make('text', { x:cx, y:cy, class:'label' });
      t.textContent = query;
      nodesLayer.appendChild(t);
      const b = t.getBBox();
      const rect = make('rect', {
        x: b.x - padding,
        y: b.y - padding,
        width:  b.width  + padding*2,
        height: b.height + padding*2,
        class: 'node-box'
      });
      nodesLayer.insertBefore(rect, t);
    })();
  
    // draw outer nodes and edges
    results.forEach((txt,i) => {
      const angle = startAngle + i*(2*Math.PI/5);
      const x     = cx + R * Math.cos(angle);
      const y     = cy + R * Math.sin(angle);
  
      // edge
      edgesLayer.appendChild(make('line',{
        x1: cx, y1: cy, x2: x, y2: y, class: 'edge'
      }));
  
      // text
      const t = make('text',{ x, y, class:'label' });
      t.textContent = txt;
      nodesLayer.appendChild(t);
  
      // box
      const b = t.getBBox();
      const rect = make('rect',{
        x: b.x - padding,
        y: b.y - padding,
        width:  b.width  + padding*2,
        height: b.height + padding*2,
        class: 'node-box'
      });
      nodesLayer.insertBefore(rect, t);
  
      [rect, t].forEach(el => 
        el.addEventListener('click', () => {
          logClick(txt);   // use the text you’re clicking on
          input.value = txt;
          form.submit();
        })
      );
    });

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
    
        // If you're using AJAX to fetch + draw, do this instead:
        // fetch(`/graph-json?query=${encodeURIComponent(randomQuery)}`)
        //   .then(res => res.json())
        //   .then(({ query, results }) => {
        //     loadNewGraph(query, results);
        //   });
      });
    });
    

    
  
  })();