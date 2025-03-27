import pandas as pd


class FilterTracker:
    def __init__(self):
        # Dictionary to store filters applied by the user
        self.filters = {}  # Format: {column_name: list_of_values}

    def apply_filter(self, column_name, values):
        """
        Apply a filter to a specific column.

        Args:
            column_name (str): The column to filter.
            values (list): The values to filter by.
        """
        self.filters[column_name] = values

    def remove_filter(self, column_name):
        """
        Remove a filter from a specific column.

        Args:
            column_name (str): The column to remove the filter from.
        """
        if column_name in self.filters:
            del self.filters[column_name]

    def get_filters(self):
        """
        Retrieve all applied filters.

        Returns:
            dict: A dictionary of applied filters.
        """
        return self.filters

    def is_filtered(self, column_name):
        """
        Check if a column is filtered.

        Args:
            column_name (str): The column name to check.
        
        Returns:
            bool: True if the column is filtered, False otherwise.
        """
        return column_name in self.filters


class DataFilter:
    def __init__(self, df):
        self.df = df
        self.filter_tracker = FilterTracker()

    def apply_filter(self, column_name, values):
        self.filter_tracker.apply_filter(column_name, values)

    def get_filtered_data(self):
        filtered_df = self.df.copy()
        
        # Apply all filters stored in FilterTracker
        for column_name, values in self.filter_tracker.get_filters().items():
            filtered_df = filtered_df[filtered_df[column_name].astype(str).isin([str(v) for v in values])]
        
        return filtered_df

    def get_data_by_column(self, column_name):
        """
        Get filtered or unfiltered data for a specific column.
        """
        if self.filter_tracker.is_filtered(column_name):
            # Return filtered data for the column
            return self.get_filtered_data()[column_name]
        else:
            # Return all data for the column
            return self.df[column_name]
