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

  // Initialize Date Range Picker (if jQuery is available)
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

  // Initialize Native Date Pickers - no jQuery required
  const initializeNativeDatePickers = () => {
    // For absence form
    const startDateInput = document.getElementById('id_start');
    const endDateInput = document.getElementById('id_end');
    
    if (startDateInput) {
      // Set attributes for date input
      startDateInput.setAttribute('type', 'date');
      startDateInput.addEventListener('change', function() {
        // Set minimum date for end date picker
        if (endDateInput && this.value) {
          endDateInput.min = this.value;
        }
      });
    }
    
    if (endDateInput) {
      // Set attributes for date input
      endDateInput.setAttribute('type', 'date');
      if (startDateInput && startDateInput.value) {
        endDateInput.min = startDateInput.value;
      }
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
    initializeNativeDatePickers();
    
    // Initialize jQuery-dependent features if jQuery is available
    if (typeof $ !== 'undefined') {
      initializeDateRangePicker();
    }
  });
})();

function executeBulkAction() {
  const bulkActionForm = document.getElementById('bulkActionForm');
  if (!bulkActionForm) {
      console.error('Bulk action form not found');
      return;
  }

  const selectedCheckboxes = document.querySelectorAll('.item-checkbox:checked');
  const selectedIds = Array.from(selectedCheckboxes).map(cb => cb.value);
  const action = document.getElementById('bulkAction').value;

  if (selectedIds.length === 0) {
      alert('الرجاء اختيار عنصر واحد على الأقل');
      return;
  }

  if (!action) {
      alert('الرجاء اختيار إجراء');
      return;
  }

  if (action === 'delete' && !confirm('هل أنت متأكد من حذف العناصر المحددة؟')) {
      return;
  }

  document.getElementById('selectedIds').value = JSON.stringify(selectedIds);
  document.getElementById('selectedAction').value = action;
  bulkActionForm.submit();
}

// Handle row clicks to navigate to data-link URL
function clickHandler(event) {
    const row = event.currentTarget;
    const link = row.getAttribute('data-link');
    if (link) {
        window.location.href = link;
    }
}

// Initialize bulk action functionality
document.addEventListener('DOMContentLoaded', function() {
  const selectAll = document.getElementById('selectAll');
  if (selectAll) {
      selectAll.addEventListener('change', function() {
          const checkboxes = document.querySelectorAll('.item-checkbox');
          checkboxes.forEach(checkbox => checkbox.checked = this.checked);
      });
  }

  // Initialize row checkboxes
  const rowCheckboxes = document.querySelectorAll('.item-checkbox');
  rowCheckboxes.forEach(checkbox => {
      checkbox.addEventListener('change', function() {
          const allChecked = Array.from(rowCheckboxes).every(cb => cb.checked);
          if (selectAll) {
              selectAll.checked = allChecked;
          }
      });
  });
});


