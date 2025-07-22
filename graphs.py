import numpy as np
import pandas as pd
from datetime import datetime

# Helper function to get irradiance data for STELLA-1.1
def get_irradiance_st1(batch_number, time_prefix_input, df):
    """
    Retrieves irradiance data for STELLA-1.1 based on batch number and time prefix.

    Args:
        batch_number: The batch number to filter by.
        time_prefix_input: The input date string from the form (e.g., '2023-07-17' or '2023-07-17 10:00').
        df: The pandas DataFrame containing STELLA-1.1 data.

    Returns:
        A list of irradiance values for the specified entry, or zeros if not found.
    """
    irradiance_list_st1 = [0.0] * 12 # Initialize with floats

    time_prefix_input_stripped = time_prefix_input.strip()
    formatted_time_prefix = ""

    try:
        if ' ' in time_prefix_input_stripped:
            dt_obj = datetime.strptime(time_prefix_input_stripped, '%Y-%m-%d %H:%M')
            formatted_time_prefix = dt_obj.strftime('%Y%m%dT%H')
        else:
            dt_obj = datetime.strptime(time_prefix_input_stripped, '%Y-%m-%d')
            formatted_time_prefix = dt_obj.strftime('%Y%m%d') + 'T'
    except ValueError:
        print(f"DEBUG: Date parsing failed for input '{time_prefix_input_stripped}'. This might be due to an incorrect format or empty input.")

    print(f"DEBUG (STELLA-1.1): Attempting to filter with batch={batch_number}, formatted_time_prefix='{formatted_time_prefix}'")
    print(f"DEBUG (STELLA-1.1): Columns available in DataFrame: {df.columns.tolist()}")

    TIMESTAMP_COL_ST1 = 'timestamp_iso8601'
    BATCH_COL_ST1 = 'batch_number'

    if TIMESTAMP_COL_ST1 not in df.columns:
        print(f"ERROR: '{TIMESTAMP_COL_ST1}' column not found in STELLA-1.1 DataFrame. Please check CSV header.")
        return irradiance_list_st1
    if BATCH_COL_ST1 not in df.columns:
        print(f"ERROR: '{BATCH_COL_ST1}' column not found in STELLA-1.1 DataFrame. Please check CSV header.")
        return irradiance_list_st1

    df[TIMESTAMP_COL_ST1] = df[TIMESTAMP_COL_ST1].astype(str).str.strip()
    print(f"DEBUG (STELLA-1.1): First 5 {TIMESTAMP_COL_ST1} values: {df[TIMESTAMP_COL_ST1].head().tolist()}")

    try:
        filtered_row = df[(df[BATCH_COL_ST1] == int(batch_number)) &
                          (df[TIMESTAMP_COL_ST1].str.startswith(formatted_time_prefix))]
    except ValueError as e:
        print(f"ERROR: Value conversion error during filtering ({BATCH_COL_ST1} to int?): {e}")
        return irradiance_list_st1

    if not filtered_row.empty:
        row = filtered_row.iloc[0]
        expected_cols = [
            'irradiance_450nm_blue_irradiance_uW_per_cm_squared',
            'irradiance_500nm_cyan_irradiance_uW_per_cm_squared',
            'irradiance_550nm_green_irradiance_uW_per_cm_squared',
            'irradiance_570nm_yellow_irradiance_uW_per_cm_squared',
            'irradiance_600nm_orange_irradiance_uW_per_cm_squared',
            'irradiance_610nm_orange_irradiance_uW_per_cm_squared',
            'irradiance_650nm_red_irradiance_uW_per_cm_squared',
            'irradiance_680nm_near_infrared_irradiance_uW_per_cm_squared',
            'irradiance_730nm_near_infrared_irradiance_uW_per_cm_squared',
            'irradiance_760nm_near_infrared_irradiance_uW_per_cm_squared',
            'irradiance_810nm_near_infrared_irradiance_uW_per_cm_squared',
            'irradiance_860nm_near_infrared_irradiance_uW_per_cm_squared'
        ]
        if all(col in row.index for col in expected_cols):
            irradiance_list_st1[0] = row['irradiance_450nm_blue_irradiance_uW_per_cm_squared']
            irradiance_list_st1[1] = row['irradiance_500nm_cyan_irradiance_uW_per_cm_squared']
            irradiance_list_st1[2] = row['irradiance_550nm_green_irradiance_uW_per_cm_squared']
            irradiance_list_st1[3] = row['irradiance_570nm_yellow_irradiance_uW_per_cm_squared']
            irradiance_list_st1[4] = row['irradiance_600nm_orange_irradiance_uW_per_cm_squared']
            irradiance_list_st1[5] = row['irradiance_610nm_orange_irradiance_uW_per_cm_squared']
            irradiance_list_st1[6] = row['irradiance_650nm_red_irradiance_uW_per_cm_squared']
            irradiance_list_st1[7] = row['irradiance_680nm_near_infrared_irradiance_uW_per_cm_squared']
            irradiance_list_st1[8] = row['irradiance_730nm_near_infrared_irradiance_uW_per_cm_squared']
            irradiance_list_st1[9] = row['irradiance_760nm_near_infrared_irradiance_uW_per_cm_squared']
            irradiance_list_st1[10] = row['irradiance_810nm_near_infrared_irradiance_uW_per_cm_squared']
            irradiance_list_st1[11] = row['irradiance_860nm_near_infrared_irradiance_uW_per_cm_squared']
            print(f"DEBUG (STELLA-1.1): Data found and extracted for batch {batch_number}.")
        else:
            print(f"ERROR: One or more expected irradiance columns missing in filtered row for STELLA-1.1. Check your STELLA-1.1 CSV for these columns.")
            print(f"Row columns: {row.index.tolist()}")
    else:
        print(f"DEBUG (STELLA-1.1): No data found for batch {batch_number} and time prefix '{formatted_time_prefix}'. This is likely due to the date/time not matching any entries in the CSV.")
        print(f"DEBUG (STELLA-1.1): DataFrame head for context:\n{df.head()}")

    return irradiance_list_st1

# Helper function to get irradiance data for STELLA-Q2
def get_irradiance_stq2(batch_number, time_prefix_input, df):
    """
    Retrieves irradiance data for STELLA-Q2 based on batch number and time prefix,
    averaging across attempts 1, 2, and 3.

    Args:
        batch_number: The batch number to filter by.
        time_prefix_input: The input date string from the form (e.g., '2023-07-17' or '2023-07-17 10:00').
        df: The pandas DataFrame containing STELLA-Q2 data.

    Returns:
        A numpy array of averaged irradiance values, or zeros if not found.
    """
    wavelengths_count = 18
    all_attempts_irrad = []

    time_prefix_input_stripped = time_prefix_input.strip()
    formatted_time_prefix = ""

    try:
        if ' ' in time_prefix_input_stripped:
            dt_obj = datetime.strptime(time_prefix_input_stripped, '%Y-%m-%d %H:%M')
            formatted_time_prefix = dt_obj.strftime('%Y%m%dT%H')
        else:
            dt_obj = datetime.strptime(time_prefix_input_stripped, '%Y-%m-%d')
            formatted_time_prefix = dt_obj.strftime('%Y%m%d') + 'T'
    except ValueError:
        print(f"DEBUG: Date parsing failed for input '{time_prefix_input_stripped}'. This might be due to an incorrect format or empty input.")

    print(f"DEBUG (STELLA-Q2): Attempting to filter with batch={batch_number}, formatted_time_prefix='{formatted_time_prefix}'")
    print(f"DEBUG (STELLA-Q2): Columns available in DataFrame: {df.columns.tolist()}")

    if 'iso8601_utc' not in df.columns:
        print("ERROR: 'iso8601_utc' column not found in STELLA-Q2 DataFrame.")
        print(f"Available columns: {df.columns.tolist()}")
        return np.zeros(wavelengths_count)

    df['iso8601_utc'] = df['iso8601_utc'].astype(str).str.strip()
    print(f"DEBUG (STELLA-Q2): First 5 iso8601_utc values: {df['iso8601_utc'].head().tolist()}")

    for attempt in [1, 2, 3]:
        try:
            filtered_data = df[(df['batch'] == int(batch_number)) &
                               (df['iso8601_utc'].str.startswith(formatted_time_prefix)) &
                               (df['mmn'] == attempt)]

            if not filtered_data.empty:
                if 'irrad.uW/(cm^2)' not in filtered_data.columns:
                    print(f"ERROR: 'irrad.uW/(cm^2)' column not found in filtered data for STELLA-Q2 (attempt {attempt}).")
                    continue

                irrad_values = filtered_data['irrad.uW/(cm^2)'].values
                if len(irrad_values) >= wavelengths_count:
                    all_attempts_irrad.append(irrad_values[:wavelengths_count])
                    print(f"DEBUG (STELLA-Q2): Data found for attempt {attempt}.")
                else:
                    print(f"DEBUG (STELLA-Q2): Not enough irradiance values for batch {batch_number}, time '{formatted_time_prefix}', attempt {attempt}. Expected {wavelengths_count}, got {len(irrad_values)}. Appending zeros.")
                    all_attempts_irrad.append(np.zeros(wavelengths_count))
            else:
                print(f"DEBUG (STELLA-Q2): No data found for batch {batch_number}, time '{formatted_time_prefix}', attempt {attempt}. Appending zeros.")
                all_attempts_irrad.append(np.zeros(wavelengths_count))
        except KeyError as e:
            print(f"ERROR: Column not found during filtering for STELLA-Q2 (attempt {attempt}): {e}. Check batch or mmn column names.")
            all_attempts_irrad.append(np.zeros(wavelengths_count))
        except ValueError as e:
            print(f"ERROR: Value conversion error during filtering for STELLA-Q2 (attempt {attempt}): {e}")
            all_attempts_irrad.append(np.zeros(wavelengths_count))

    if all_attempts_irrad:
        total_list = np.mean(all_attempts_irrad, axis=0)
    else:
        total_list = np.zeros(wavelengths_count)

    print(f"DEBUG (STELLA-Q2): Final averaged irradiance list: {total_list}")
    return total_list


# Radiance calculation functions (no changes here)
def get_radiance_target(irradiance, distance):
    irradiance = np.array(irradiance)
    if distance == 0:
        return np.zeros_like(irradiance)
    radiance = (irradiance * distance**2) / (2 * np.pi * (distance/2)**2)
    return radiance

def get_radiance_of_reference(irradiance1, distance, irradiance2=None):
    irradiance1 = np.array(irradiance1)
    if irradiance2 is not None:
        irradiance2 = np.array(irradiance2)
        avr = (irradiance1 + irradiance2) / 2
    else:
        avr = irradiance1
    if distance == 0:
        return np.zeros_like(avr)
    area = 2 * np.pi * (distance / 2) ** 2
    radiance = (avr * distance**2) / area
    return radiance

def get_reflectance(rad_target, rad_reference):
    if np.any(rad_reference == 0):
        print("Warning: Reference radiance contains zero values, leading to division by zero in reflectance calculation.")
        rad_reference = np.where(rad_reference == 0, np.finfo(float).eps, rad_reference)
    return (rad_target / rad_reference)

# Calculation functions for STELLA-1.1 and STELLA-Q2 (no changes here)
def get_calculation_STELLA_1(df, obj):
    date = obj.get('date', '')
    distance = float(obj.get('distance', 1.0))
    cal1 = int(obj.get('cal1', 0))
    dp1 = int(obj.get('dp1', 0))
    cal2 = int(obj.get('cal2', 0))
    dp2 = int(obj.get('dp2', 0))

    material_irradiancy_st1 = np.array(get_irradiance_st1(dp1, date, df))
    material_irradiancy2_st1 = np.array(get_irradiance_st1(dp2, date, df))
    material_irradiancy_av = (material_irradiancy_st1 + material_irradiancy2_st1) / 2

    material_rad_st1 = np.array(get_radiance_target(material_irradiancy_av, distance))

    material_rad_wh_st1 = np.array(get_radiance_of_reference(
        get_irradiance_st1(cal1, date, df), distance, get_irradiance_st1(cal2, date, df)
    ))
    material_reflectance_st1 = np.array(get_reflectance(material_rad_st1, material_rad_wh_st1))

    return material_irradiancy_av, material_reflectance_st1

def get_calculation_STELLA_q2(df, obj):
    date = obj.get('date', '')
    distance = float(obj.get('distance', 1.0))
    cal1 = int(obj.get('cal1', 0))
    dp1 = int(obj.get('dp1', 0))
    cal2 = int(obj.get('cal2', 0))
    dp2 = int(obj.get('dp2', 0))

    material_irradiancy_stq2 = np.array(get_irradiance_stq2(dp1, date, df))
    material_irradiancy2_stq2 = np.array(get_irradiance_stq2(dp2, date, df))
    material_irradiancy_av = (material_irradiancy_stq2 + material_irradiancy2_stq2) / 2

    material_rad_stq2 = np.array(get_radiance_target(material_irradiancy_av, distance))

    material_rad_wh_stq2 = np.array(get_radiance_of_reference(
        get_irradiance_stq2(cal1, date, df), distance, get_irradiance_stq2(cal2, date, df)
    ))
    material_reflectance_stq2 = np.array(get_reflectance(material_rad_stq2, material_rad_wh_stq2))

    return material_irradiancy_av, material_reflectance_stq2


# Main functions to generate table data
def generate_table_data_stella1(df, objects):
    wavelengths_list_st1 = np.array([450, 500, 550, 570, 600, 610, 650, 680, 730, 760, 810, 860])
    table_data = []

    if df is not None and not df.empty:
        for i, obj in enumerate(objects):
            try:
                irradiance_av, reflectance = get_calculation_STELLA_1(df, obj)
                line_name = obj.get('line_name', f'Line {i+1}') # Use 'Line' as default name

                for j in range(len(wavelengths_list_st1)):
                    table_data.append({
                        'Line': line_name,
                        'Wavelength (nm)': wavelengths_list_st1[j],
                        'Irradiance (uW/cm^2)': f"{irradiance_av[j]:.2f}",
                        'Reflectance': f"{reflectance[j]:.4f}"
                    })
            except Exception as e:
                print(f"Error generating table data for STELLA-1.1 object {i}: {e}")
                # Optionally add an error entry to table_data if needed for debugging
                # table_data.append({'Line': f'Error Line {i+1}', 'Wavelength (nm)': 'N/A', 'Irradiance (uW/cm^2)': 'ERROR', 'Reflectance': 'ERROR'})

    return table_data


def generate_table_data_stellaq2(df, objects):
    wavelengths_list_stq2 = np.array([410, 435, 460, 485, 510, 535, 560, 585, 610, 645, 680, 705, 730, 760, 810, 860, 900, 940])
    table_data = []

    if df is not None and not df.empty:
        for i, obj in enumerate(objects):
            try:
                irradiance_av, reflectance = get_calculation_STELLA_q2(df, obj)
                line_name = obj.get('line_name', f'Line {i+1}') # Use 'Line' as default name

                for j in range(len(wavelengths_list_stq2)):
                    table_data.append({
                        'Line': line_name,
                        'Wavelength (nm)': wavelengths_list_stq2[j],
                        'Irradiance (uW/cm^2)': f"{irradiance_av[j]:.2f}",
                        'Reflectance': f"{reflectance[j]:.4f}"
                    })
            except Exception as e:
                print(f"Error generating table data for STELLA-Q2 object {i}: {e}")
                # Optionally add an error entry to table_data if needed for debugging
                # table_data.append({'Line': f'Error Line {i+1}', 'Wavelength (nm)': 'N/A', 'Irradiance (uW/cm^2)': 'ERROR', 'Reflectance': 'ERROR'})

    return table_data
