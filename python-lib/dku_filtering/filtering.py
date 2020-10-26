import pandas as pd
from functools import reduce


def numerical_filter(df, filter):
    conditions = []
    if filter["minValue"]:
        conditions += [df[filter['column']] >= filter['minValue']]
    if filter["maxValue"]:
        conditions += [df[filter['column']] <= filter['maxValue']]
    return conditions


def alphanum_filter(df, filter):
    conditions = []
    excluded_values = []
    for k, v in filter['excludedValues'].items():
        if k != '___dku_no_value___':
            if v:
                excluded_values += [k]
        else:
            if v:
                conditions += [~df[filter['column']].isnull()]
    if len(excluded_values) > 0:
        if filter['columnType'] == 'NUMERICAL':
            excluded_values = [float(x) for x in excluded_values]
        conditions += [~df[filter['column']].isin(excluded_values)]
    return conditions


def date_filter(df, filter):
    if filter["dateFilterType"] == "RANGE":
        return date_range_filter(df, filter)
    else:
        return special_date_filter(df, filter)


def date_range_filter(df, filter):
    conditions = []
    if filter["minValue"]:
        conditions += [df[filter['column']] >= pd.Timestamp(filter['minValue'], unit='ms')]
    if filter["maxValue"]:
        conditions += [df[filter['column']] <= pd.Timestamp(filter['maxValue'], unit='ms')]
    return conditions


def special_date_filter(df, filter):
    conditions = []
    excluded_values = []
    for k, v in filter['excludedValues'].items():
        if v:
            excluded_values += [k]
    if len(excluded_values) > 0:
        if filter["dateFilterType"] == "YEAR":
            conditions += [~df[filter['column']].dt.year.isin(excluded_values)]
        elif filter["dateFilterType"] == "QUARTER_OF_YEAR":
            conditions += [~df[filter['column']].dt.quarter.isin([int(k)+1 for k in excluded_values])]
        elif filter["dateFilterType"] == "MONTH_OF_YEAR":
            conditions += [~df[filter['column']].dt.month.isin([int(k)+1 for k in excluded_values])]
        elif filter["dateFilterType"] == "WEEK_OF_YEAR":
            conditions += [~df[filter['column']].dt.week.isin([int(k)+1 for k in excluded_values])]
        elif filter["dateFilterType"] == "DAY_OF_MONTH":
            conditions += [~df[filter['column']].dt.day.isin([int(k)+1 for k in excluded_values])]
        elif filter["dateFilterType"] == "DAY_OF_WEEK":
            conditions += [~df[filter['column']].dt.dayofweek.isin(excluded_values)]
        elif filter["dateFilterType"] == "HOUR_OF_DAY":
            conditions += [~df[filter['column']].dt.hour.isin(excluded_values)]
        else:
            raise Exception("Unknown date filter.")

    return conditions


def apply_filter_conditions(df, conditions):
    """
    return a function to apply filtering conditions on df
    """
    if len(conditions) == 0:
        return df
    elif len(conditions) == 1:
        return df[conditions[0]]
    else:
        return df[reduce(lambda c1, c2: c1 & c2, conditions[1:], conditions[0])]


def filter_dataframe(df, filters):
    """
    return the input dataframe df with filters applied to it
    """
    for filter in filters:
        try:
            if filter["filterType"] == "NUMERICAL_FACET":
                df = apply_filter_conditions(df, numerical_filter(df, filter))
            elif filter["filterType"] == "ALPHANUM_FACET":
                df = apply_filter_conditions(df, alphanum_filter(df, filter))
            elif filter["filterType"] == "DATE_FACET":
                df = apply_filter_conditions(df, date_filter(df, filter))
        except Exception as e:
            raise Exception("Error with filter on column {} - {}".format(filter["column"], e))
    if df.empty:
        raise Exception("Dataframe is empty after filtering")
    return df
