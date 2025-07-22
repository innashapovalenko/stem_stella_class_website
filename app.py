from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, get_flashed_messages
import pandas as pd
import os
import json # Keep json for general data handling if needed, though not for plotly figures anymore
import graphs # Assuming you have this file in the same directory

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = 'my_secret_key_here' # Needed for flashing messages

# Global storage for uploaded file paths and data points
data_storage = {
    'stella1': {'file_path': None, 'objects': []}, # Store file path instead of df
    'stellaq2': {'file_path': None, 'objects': []} # Store file path instead of df
}

# Helper function to generate an HTML table from a list of dictionaries
def generate_html_table(data_list, device_name):
    if not data_list:
        return f"<p class='text-center text-gray-500'>No data to display for {device_name} table. Upload a CSV and add a line.</p>"

    # Determine wavelengths based on device
    if device_name == 'stella1':
        wavelengths = [450, 500, 550, 570, 600, 610, 650, 680, 730, 760, 810, 860]
    elif device_name == 'stellaq2':
        wavelengths = [410, 435, 460, 485, 510, 535, 560, 585, 610, 645, 680, 705, 730, 760, 810, 860, 900, 940]
    else:
        return "<p class='text-center text-gray-500'>Unknown device for table generation.</p>"

    # Get unique line names, sorted for consistent column order
    line_names = sorted(list(set(item['Line'] for item in data_list)))

    # Group data by wavelength and then by line
    # This will be a dictionary where keys are wavelengths
    # and values are dictionaries of {line_name: {'irradiance': val, 'reflectance': val}}
    pivoted_data = {wl: {} for wl in wavelengths}
    for item in data_list:
        wl = item['Wavelength (nm)']
        line = item['Line']
        if wl in pivoted_data: # Ensure wavelength is one we expect
            pivoted_data[wl][line] = {
                'irradiance': item['Irradiance (uW/cm^2)'],
                'reflectance': item['Reflectance']
            }

    table_html = "<table class='min-w-full bg-white border border-gray-300 rounded-md shadow-sm'>"
    table_html += "<thead><tr class='bg-gray-100'>"
    table_html += "<th class='py-2 px-4 border-b text-left text-sm font-semibold text-gray-700'>Wavelength (nm)</th>"
    for line_name in line_names:
        table_html += f"<th class='py-2 px-4 border-b text-left text-sm font-semibold text-gray-700'>{line_name} (Irradiance)</th>"
        table_html += f"<th class='py-2 px-4 border-b text-left text-sm font-semibold text-gray-700'>{line_name} (Reflectance)</th>"
    table_html += "</tr></thead>"
    table_html += "<tbody>"

    for wl in wavelengths:
        table_html += "<tr>"
        table_html += f"<td class='py-2 px-4 border-b text-sm text-gray-800'>{wl}</td>"
        for line_name in line_names:
            line_data = pivoted_data[wl].get(line_name, {})
            irrad_value = line_data.get('irradiance', 'N/A')
            reflect_value = line_data.get('reflectance', 'N/A')
            table_html += f"<td class='py-2 px-4 border-b text-sm text-gray-800'>{irrad_value}</td>"
            table_html += f"<td class='py-2 px-4 border-b text-sm text-gray-800'>{reflect_value}</td>"
        table_html += "</tr>"

    table_html += "</tbody></table>"
    return table_html


# Home page - This route renders the main page and prepares the tables
@app.route('/')
def index():
    tables = {}

    for device in ['stella1', 'stellaq2']:
        df = None
        if data_storage[device]['file_path']:
            try:
                df = pd.read_csv(data_storage[device]['file_path'])
                df.columns = df.columns.str.strip()
                print(f"DEBUG (app.py - index): Successfully reloaded DataFrame for {device} from {data_storage[device]['file_path']}")
            except Exception as e:
                print(f"ERROR (app.py - index): Could not reload DataFrame for {device} from {data_storage[device]['file_path']}: {e}")

        objects = data_storage[device]['objects']

        print(f"DEBUG (app.py - index): For device '{device}':")
        print(f"  df is None: {df is None}")
        if df is not None:
            print(f"  df is empty: {df.empty}")
            print(f"  df columns: {df.columns.tolist()}")
        print(f"  objects count: {len(objects)}")

        table_data = []

        # Only generate table data if DataFrame is loaded and not empty
        if df is not None and not df.empty:
            if device == 'stella1':
                table_data = graphs.generate_table_data_stella1(df, objects)
            elif device == 'stellaq2':
                table_data = graphs.generate_table_data_stellaq2(df, objects)

        tables[device] = generate_html_table(table_data, device)

    flashed_messages = get_flashed_messages(with_categories=True)

    return render_template('index.html',
                           table1_html=tables['stella1'],
                           table2_html=tables['stellaq2'],
                           flashed_messages=flashed_messages)

# Route to handle file uploads for a specific device (stella1 or stellaq2)
@app.route('/upload/<device>', methods=['POST'])
def upload_file(device):
    if 'file' not in request.files:
        flash('No file part in the request.', 'error')
        return redirect(url_for('index'))

    file = request.files['file']

    if file.filename == '':
        flash('No selected file.', 'warning')
        return redirect(url_for('index'))

    if file and device in data_storage:
        try:
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{device}.csv')
            file.save(file_path)
            data_storage[device]['file_path'] = file_path

            df_check = pd.read_csv(file_path)
            df_check.columns = df_check.columns.str.strip()
            print(f"File uploaded successfully for {device} and saved to {file_path}. Columns loaded: {df_check.columns.tolist()}")
            flash(f"File for {device.upper()} uploaded successfully!", 'success')

        except Exception as e:
            print(f"Error saving or reading CSV file for {device}: {e}")
            flash(f"Error uploading file for {device.upper()}: {e}", 'error')
    else:
        print(f"File not found or invalid device: {device}")
        flash(f"File not found or invalid device: {device}", 'error')

    return redirect(url_for('index'))

# Add Object
@app.route('/add_object/<device>', methods=['POST'])
def add_object(device):
    if device in data_storage:
        obj_data = request.form.to_dict()
        data_storage[device]['objects'].append(obj_data)
        print(f"Added object for {device}: {obj_data}")
        flash(f"New line '{obj_data.get('line_name', 'Unnamed Line')}' added to {device.upper()} table!", 'info')
    else:
        print(f"Invalid device for adding object: {device}")
        flash(f"Invalid device for adding object: {device}", 'error')
    return redirect(url_for('index'))

# Remove Object
@app.route('/remove_object/<device>/<int:idx>', methods=['POST'])
def remove_object(device, idx):
    try:
        if 0 <= idx < len(data_storage[device]['objects']):
            removed_obj = data_storage[device]['objects'].pop(idx)
            flash(f"Line '{removed_obj.get('line_name', 'Unnamed Line')}' removed from {device.upper()} table.", 'info')
        else:
            flash(f"Invalid line index for {device.upper()}.", 'warning')
    except IndexError:
        flash(f"Invalid line index for {device.upper()}.", 'warning')
    return redirect(url_for('index'))

# NEW: Route to clear all graph objects (lines) for a specific device
@app.route('/clear_objects/<device>', methods=['POST'])
def clear_objects(device):
    if device in data_storage:
        data_storage[device]['objects'] = []
        if data_storage[device]['file_path'] and os.path.exists(data_storage[device]['file_path']):
            os.remove(data_storage[device]['file_path'])
            data_storage[device]['file_path'] = None
            flash(f"All lines and data file for {device.upper()} cleared!", 'success')
            print(f"Cleared all objects and removed file for {device}.")
        else:
            flash(f"All lines for {device.upper()} cleared!", 'success')
            print(f"Cleared all objects for {device}.")
    else:
        print(f"Invalid device for clearing objects: {device}")
        flash(f"Invalid device for clearing objects: {device}", 'error')
    return redirect(url_for('index'))

# Serve data to frontend for plotly (this route might not be strictly needed with current setup)
@app.route('/get_data/<device>')
def get_data(device):
    df = None
    if device in data_storage and data_storage[device]['file_path']:
        try:
            df = pd.read_csv(data_storage[device]['file_path'])
            df.columns = df.columns.str.strip()
        except Exception as e:
            print(f"ERROR (get_data): Could not load DataFrame for {device}: {e}")
            return jsonify([])

    if df is None or df.empty:
        return jsonify([])

    return jsonify(df.to_dict(orient='records'))


if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True)
