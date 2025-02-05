/* globals Chart:false */

(() => {
  'use strict'

  // Graphs
  const initializeChart = () => {
    const ctx = document.getElementById('myChart')
    if (!ctx) return;

    // eslint-disable-next-line no-unused-vars
    const myChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: [
          'Sunday',
          'Monday',
          'Tuesday',
          'Wednesday',
          'Thursday',
          'Friday',
          'Saturday'
        ],
        datasets: [{
          data: [
            15339,
            21345,
            18483,
            24003,
            23489,
            24092,
            12034
          ],
          lineTension: 0,
          backgroundColor: 'transparent',
          borderColor: '#007bff',
          borderWidth: 4,
          pointBackgroundColor: '#007bff'
        }]
      },
      options: {
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            boxPadding: 3
          }
        }
      }
    })
  }

  // Initialize Date Range Picker
  const initializeDateRangePicker = () => {
    const dateRangeInput = $('input[name="daterange"]');
    if (dateRangeInput.length) {
      dateRangeInput.daterangepicker({
        opens: 'left',
        locale: {
          format: 'YYYY-MM-DD'
        },
        autoApply: true,
        showDropdowns: true
      }, function(start, end, label) {
        console.log("Selected date range: " + start.format('YYYY-MM-DD') + ' to ' + end.format('YYYY-MM-DD'));
      });
    }
  }

  // Initialize Date Pickers
  const initializeDatePickers = () => {
    // For absence form
    const startDateInput = $('#id_start');
    const endDateInput = $('#id_end');
    
    if (startDateInput.length) {
      startDateInput.datepicker({
        format: 'yyyy-mm-dd',
        autoclose: true
      });
    }
    
    if (endDateInput.length) {
      endDateInput.datepicker({
        format: 'yyyy-mm-dd',
        autoclose: true
      });
    }
  }

  // Sidebar functionality
  const initializeSidebar = () => {
    // Handle sidebar toggle on mobile
    const sidebarToggle = document.querySelector('[data-bs-toggle="offcanvas"]');
    if (sidebarToggle) {
      sidebarToggle.addEventListener('click', function() {
        document.querySelector('.sidebar').classList.toggle('show');
      });
    }

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function(event) {
      const sidebar = document.querySelector('.sidebar');
      const toggle = document.querySelector('[data-bs-toggle="offcanvas"]');
      if (sidebar && toggle && window.innerWidth < 768 && 
          !sidebar.contains(event.target) && 
          !toggle.contains(event.target)) {
        sidebar.classList.remove('show');
      }
    });
  }

  // Handle submenu animations
  const initializeSubmenus = () => {
    const submenuToggles = document.querySelectorAll('.has-submenu > .nav-link');
    
    submenuToggles.forEach(toggle => {
      toggle.addEventListener('click', function(e) {
        const submenuIcon = this.querySelector('.submenu-icon');
        const isExpanded = this.getAttribute('aria-expanded') === 'true';
        
        // Animate the chevron icon
        if (submenuIcon) {
          submenuIcon.style.transform = isExpanded ? 'rotate(0deg)' : 'rotate(-180deg)';
        }
      });
    });
  }

  // Set active state based on current URL
  const setActiveNavItem = () => {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.sidebar .nav-link');
    
    navLinks.forEach(link => {
      if (link.getAttribute('href') === currentPath) {
        link.classList.add('active');
        // If in submenu, expand parent
        const parentSubmenu = link.closest('.submenu');
        if (parentSubmenu) {
          parentSubmenu.classList.add('show');
          const parentToggle = parentSubmenu.previousElementSibling;
          if (parentToggle) {
            parentToggle.setAttribute('aria-expanded', 'true');
          }
        }
      }
    });
  }

  // Document ready handler
  document.addEventListener('DOMContentLoaded', function() {
    initializeChart();
    initializeSidebar();
    initializeSubmenus();
    setActiveNavItem();
    
    // Initialize jQuery-dependent features if jQuery is available
    if (typeof $ !== 'undefined') {
      initializeDateRangePicker();
      initializeDatePickers();
    }
  });
})();


document.addEventListener('DOMContentLoaded', function() {
  // Get DOM elements
  const selectAll = document.getElementById('select-all');
  const itemCheckboxes = document.querySelectorAll('.item-checkbox');
  const actionForm = document.getElementById('actionForm');
  const selectedItemsInput = document.getElementById('selectedItems');
  
  // Handle "Select All" checkbox
  selectAll.addEventListener('change', function() {
      itemCheckboxes.forEach(checkbox => {
          checkbox.checked = this.checked;
      });
  });

  // Update "Select All" when individual checkboxes change
  itemCheckboxes.forEach(checkbox => {
      checkbox.addEventListener('change', function() {
          selectAll.checked = [...itemCheckboxes].every(cb => cb.checked);
      });
  });

  // Handle form submission
  actionForm.addEventListener('submit', function(e) {
      e.preventDefault();

      // Get selected items
      const selectedItems = [...itemCheckboxes]
          .filter(cb => cb.checked)
          .map(cb => cb.value);

      // Validate selection
      if (selectedItems.length === 0) {
          alert('Please select at least one user');
          return;
      }

      // Get selected action
      const selectedAction = this.querySelector('.action-select').value;
      if (!selectedAction) {
          alert('Please select an action');
          return;
      }

      // Update hidden input with selected items
      selectedItemsInput.value = selectedItems.join(',');

      // Submit the form
      this.submit();
  });

  // Row click handler (existing functionality)
  window.clickHandler = function(event) {
      if (!event.target.closest('input[type="checkbox"]') && 
          !event.target.closest('.action-buttons')) {
          const link = event.currentTarget.dataset.link;
          if (link) window.location.href = link;
      }
  };
});