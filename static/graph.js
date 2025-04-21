(function(){

    // grab the data you embedded into the page
    const { query, results } = window.BELIEF_DATA;
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
  
      [rect, t].forEach(el => 
        el.addEventListener('click', () => {
          input.value = query;
          form.submit();
        })
      );
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
          input.value = txt;
          form.submit();
        })
      );
    });
  
  })();