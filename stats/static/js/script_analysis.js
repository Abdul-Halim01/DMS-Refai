// JavaScript for Per-Plot Filtering

  $(document).ready(function() {
      // ... keep existing global filter code ...

      // Handle filter mode changes
      $('.filter-mode').change(function() {
          const target = $(this).data('target');
          const mode = $(this).val();
          
          // Hide all optional filter sections first
          $(`#filter-by-other-${target}, #compare-by-${target}`).hide();
          $(`#filter-values-${target}`).parent().show();
          
          if (mode === 'self') {
              // Get values for the target column itself
              $.get(urls.get_unique_values, { column: target }, function (data) {
                  const filterValues = $(`#filter-values-${target}`);
                  filterValues.empty();
                  if (data.values) {
                      data.values.forEach(function(value) {
                          filterValues.append(new Option(value, value));
                      });
                  }
              });
          } else if (mode === 'other') {
              $(`#filter-by-other-${target}`).show();
              $(`#filter-values-${target}`).empty();
              
              // Reset the filter column selection
              $(`#filter-column-${target}`).val('');
          } else if (mode === 'compare') {
              $(`#compare-by-${target}`).show();
              $(`#filter-values-${target}`).parent().hide();
          }
      });

      // Handle filter column selection
      $('.filter-column').change(function() {
          const target = $(this).data('target');
          const selectedColumn = $(this).val();
          
          console.log('Filter column selected:', {
              target: target,
              selectedColumn: selectedColumn
          });
          
          if (selectedColumn) {
            $.get(urls.get_unique_values, { column: selectedColumn }, function (data) {

                  console.log('Received unique values:', data);
                  const filterValues = $(`#filter-values-${target}`);
                  filterValues.empty();
                  if (data.values) {
                      data.values.forEach(function(value) {
                          filterValues.append(new Option(value, value));
                      });
                  }
              }).fail(function(jqXHR, textStatus, errorThrown) {
                  console.error('Error fetching values:', textStatus, errorThrown);
              });
          } else {
              $(`#filter-values-${target}`).empty();
          }
      });

      // Add handler for compare column selection
      $('.compare-column').change(function() {
          const target = $(this).data('target');
          const compareColumn = $(this).val();
          
          if (compareColumn) {
              // Get column types and update plot options
              $.get(urls.get_column_types, { target: target, compare_column: compareColumn }, function (data) {

                  updatePlotOptions(target, compareColumn, data.column_types);
              });
          } else {
              // Hide plot options if no column selected
              $(`#compare-by-${target} .plot-type-selector`).hide();
              $(`#compare-by-${target} .plot-options`).hide();
          }
      });

      // Function to update plot options based on column types
      function updatePlotOptions(target, compareColumn, columnTypes) {
          const plotTypeSelect = $(`#plot-type-${target}`);
          const plotTypeContainer = $(`#compare-by-${target} .plot-type-selector`);
          const plotOptions = $(`#compare-by-${target} .plot-options`);
          
          plotTypeSelect.empty();
          
          const targetType = columnTypes.target;
          const compareType = columnTypes.compare;
          
          // Add appropriate plot options based on column types
          if (targetType === 'numeric' && compareType === 'numeric') {
              plotTypeSelect.append(new Option('Scatter Plot', 'scatter'));
              plotTypeSelect.append(new Option('Hexbin Plot', 'hexbin'));
              plotTypeSelect.append(new Option('2D Density', 'density'));
              plotTypeSelect.append(new Option('Line Plot', 'line'));
          } else if (targetType === 'numeric' && compareType === 'categorical') {
              plotTypeSelect.append(new Option('Box Plot', 'box'));
              plotTypeSelect.append(new Option('Violin Plot', 'violin'));
              plotTypeSelect.append(new Option('Bar Plot (Mean)', 'bar'));
              plotTypeSelect.append(new Option('Strip Plot', 'strip'));
          } else if (targetType === 'categorical' && compareType === 'numeric') {
              plotTypeSelect.append(new Option('Box Plot', 'box'));
              plotTypeSelect.append(new Option('Violin Plot', 'violin'));
              plotTypeSelect.append(new Option('Bar Plot (Mean)', 'bar'));
              plotTypeSelect.append(new Option('Strip Plot', 'strip'));
          } else {
              // Both categorical
              plotTypeSelect.append(new Option('Heatmap', 'heatmap'));
              plotTypeSelect.append(new Option('Grouped Bar Plot', 'grouped_bar'));
              plotTypeSelect.append(new Option('Stacked Bar Plot', 'stacked_bar'));
              plotTypeSelect.append(new Option('Treemap', 'treemap'));
          }
          
          plotTypeContainer.show();
          plotOptions.show();
          
          // Trigger change to update plot
          plotTypeSelect.trigger('change');
      }

      // Handle plot type changes
      $('.plot-type').change(function() {
          const target = $(this).data('target');
          const plotType = $(this).val();
          const compareColumn = $(`#compare-column-${target}`).val();
          
          // Show/hide additional options based on plot type
          const aggMethodDiv = $(`#compare-by-${target} .aggregation-method`);
          const colorByDiv = $(`#compare-by-${target} .color-by`);
          
          if (['bar', 'grouped_bar', 'stacked_bar'].includes(plotType)) {
              aggMethodDiv.show();
          } else {
              aggMethodDiv.hide();
          }
          
          if (['scatter', 'strip'].includes(plotType)) {
              colorByDiv.show();
          } else {
              colorByDiv.hide();
          }
          
          // Update plot
          updateComparisonPlot(target, compareColumn, plotType);
      });

      // Function to update the comparison plot
      function updateComparisonPlot(target, compareColumn, plotType) {
          const aggMethod = $(`#agg-method-${target}`).val();
          const colorColumn = $(`#color-column-${target}`).val();
          
          $.ajax({
              url: urls.compare_plot,
              data: {
                  target: target,
                  compare_column: compareColumn,
                  plot_type: plotType,
                  agg_method: aggMethod,
                  color_column: colorColumn
              },
              success: function(response) {
                  if (response.plot_html) {
                      $(`#plot-container-${target}`).html(response.plot_html);
                  }
              },
              error: function(xhr) {
                  console.error('Error updating plot:', xhr.responseText);
              }
          });
      }

      $(document).ready(function () {
        // Initialize filter values for 'self' mode on page load
        $('.filter-mode').each(function () {
            const target = $(this).data('target');
            $.get(getUniqueValuesUrl, { column: target }, function (data) {
                const filterValues = $(`#filter-values-${target}`);
                filterValues.empty();
                if (data.values) {
                    data.values.forEach(function (value) {
                        filterValues.append(new Option(value, value));
                    });
                }
            });
        });
    });
    

      // Update the filter values change handler
      $('.filter-values').change(function() {
          const target = $(this).data('target');
          const mode = $(`#filter-mode-${target}`).val();
          const selectedValues = $(this).val();
          
          console.log('Filter values changed:', {
              target: target,
              mode: mode,
              selectedValues: selectedValues
          });
          
          if (selectedValues && selectedValues.length > 0) {
              let filterData = {
                  target: target,
                  mode: mode,
                  'values[]': selectedValues
              };

              if (mode === 'other') {
                  filterData.filter_column = $(`#filter-column-${target}`).val();
              }

              console.log('Sending filter request:', filterData);

              $.ajax({
                  url: urls.filter_plot,
                  method: 'GET',
                  data: filterData,
                  success: function(response) {
                      if (response.plot_html) {
                          $(`#plot-container-${target}`).html(response.plot_html);
                      }
                  },
                  error: function(xhr) {
                      console.error('Error updating plot:', xhr.responseText);
                  }
              });
          }
      });

      // Reset plot functionality
      window.resetPlot = function(col) {
          const container = $(`#plot-container-${col}`);
          const originalPlot = container.data('original-plot');
          
          // Reset the plot to original state
          container.html(originalPlot);
          
          // Reset filter controls
          $(`#filter-mode-${col}`).val('self');
          $(`#filter-by-other-${col}, #compare-by-${col}`).hide();
          
          // Reset and update filter values
          $.get(urls.get_unique_values, { column: col }, function (data) {
              const filterValues = $(`#filter-values-${col}`);
              filterValues.empty();
              if (data.values) {
                  data.values.forEach(function(value) {
                      filterValues.append(new Option(value, value));
                  });
              }
          });
      };
  });


// Add this just before the closing </body> tag

  $(document).ready(function() {
      // Store original plots
      $('.plot-container').each(function() {
          $(this).data('original-plot', $(this).html());
      });

      // Handle adding new filter rows
      $('#add-filter').click(function() {
          const filterRow = `
              <div class="filter-row">
                  <select class="global-filter-column">
                      <option value="">Select Column</option>
                      {% for col in overview.columns %}
                          <option value="{{ col }}">{{ col }}</option>
                      {% endfor %}
                  </select>
                  <select class="global-filter-values" multiple>
                  </select>
                  <button class="btn btn-secondary remove-filter">Remove</button>
              </div>
          `;
          $('#global-filters').append(filterRow);
      });

      // Handle removing filter rows
      $(document).on('click', '.remove-filter', function() {
          $(this).closest('.filter-row').remove();
      });

      // Handle column selection for global filters
      $(document).on('change', '.global-filter-column', function() {
          const column = $(this).val();
          const valuesSelect = $(this).siblings('.global-filter-values');
          
          if (column) {
            $.get(urls.get_unique_values, { column: column }, function (data){
                  valuesSelect.empty();
                  data.values.forEach(function(value) {
                      valuesSelect.append(new Option(value, value));
                  });
              });
          }
      });

      // Handle apply filters button
      $('#apply-filters').click(function() {
          const filters = [];
          $('.filter-row').each(function() {
              const column = $(this).find('.global-filter-column').val();
              const values = $(this).find('.global-filter-values').val();
              if (column && values && values.length > 0) {
                  filters.push({ column: column, values: values });
              }
          });

          const logic = $('#global-logic').val();

          $.ajax({
              url: urls.apply_global_filters,
              method: 'POST',
              data: {
                  filters: JSON.stringify(filters),
                  logic: logic,
                  csrfmiddlewaretoken: '{{ csrf_token }}'
              },
              success: function(response) {
                  if (response.plots) {
                      // Update each plot with the new filtered version
                      Object.keys(response.plots).forEach(function(col) {
                          const plotContainer = $(`#plot-container-${col}`);
                          plotContainer.html(response.plots[col]);
                          // Store the filtered state
                          plotContainer.data('filtered-plot', response.plots[col]);
                      });
                  }
              },
              error: function(xhr) {
                  console.error('Error applying filters:', xhr.responseText);
                  alert('Error applying filters. Please check the console for details.');
              }
          });
      });
  });
