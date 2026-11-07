(function () {
  "use strict";

  function rowsOf(table) {
    return Array.prototype.slice.call(table.tBodies[0] ? table.tBodies[0].rows : []);
  }

  function applyFilters(control) {
    var table = document.getElementById(control.getAttribute("data-table-filter"));
    if (!table) return;
    var query = (control.value || "").trim().toLowerCase();
    var statusSelect = document.querySelector('[data-status-filter="' + table.id + '"]');
    var status = statusSelect ? statusSelect.value : "";
    var visible = 0;
    rowsOf(table).forEach(function (row) {
      var text = row.textContent.toLowerCase();
      var rowStatus = row.getAttribute("data-status") || "";
      var show = (!query || text.indexOf(query) !== -1) && (!status || rowStatus === status);
      row.hidden = !show;
      if (show) visible += 1;
    });
    var counter = document.querySelector('[data-count-for="' + table.id + '"]');
    if (counter) counter.textContent = visible + " of " + rowsOf(table).length + " rows shown";
  }

  document.querySelectorAll("[data-table-filter]").forEach(function (control) {
    control.addEventListener("input", function () { applyFilters(control); });
    applyFilters(control);
  });

  document.querySelectorAll("[data-status-filter]").forEach(function (select) {
    select.addEventListener("change", function () {
      var table = document.getElementById(select.getAttribute("data-status-filter"));
      var search = document.querySelector('[data-table-filter="' + (table ? table.id : "") + '"]');
      if (search) applyFilters(search);
      else if (table) {
        var visible = 0;
        rowsOf(table).forEach(function (row) {
          var show = !select.value || row.getAttribute("data-status") === select.value;
          row.hidden = !show;
          if (show) visible += 1;
        });
        var counter = document.querySelector('[data-count-for="' + table.id + '"]');
        if (counter) counter.textContent = visible + " of " + rowsOf(table).length + " rows shown";
      }
    });
  });
})();
