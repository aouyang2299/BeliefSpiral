document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.belief-link').forEach(function(el) {
      el.addEventListener('click', function(e) {
        e.preventDefault();
        var value = this.textContent;
        var input = document.querySelector('input[name="query"]');
        input.value = value;
        input.focus();
      });
    });
  });