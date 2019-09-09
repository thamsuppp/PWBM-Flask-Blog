import base64
import os
from urllib.parse import quote as urlquote

from flask import Flask, send_from_directory
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import json

#Set an upload directory where uploaded files are stored
UPLOAD_DIRECTORY = "/project/app_uploaded_files"

if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)


# Normally, Dash creates its own Flask server internally. By creating our own,
# we can create a route for downloading files directly:
server = Flask(__name__)
app = dash.Dash(server=server)

#Once you have uploaded file, it is on the server path already
#Going to the server path (either by clicking link or going to URL) downloads file
@server.route("/download/<path:path>")
def download(path):
    print('download function run')
    print(path)
    #Finds file from upload directory and places it at the route
    return send_from_directory(UPLOAD_DIRECTORY, path, as_attachment=True)


app.layout = html.Div(
    [
        html.H1("File Browser"),
        html.H2("Upload"),
        dcc.Input(id = 'input', type = 'text', value = ''),
        dcc.Input(id = 'filename_input', type = 'text', value = ''),
        html.Button('Submit', id='button'),
        dcc.Upload(
            id="upload-data",
            children=html.Div(
                ["Drag and drop or click to select a file to upload."]
            ),
            style={
                "width": "100%",
                "height": "60px",
                "lineHeight": "60px",
                "borderWidth": "1px",
                "borderStyle": "dashed",
                "borderRadius": "5px",
                "textAlign": "center",
                "margin": "10px",
            },
            multiple=True,
        ),
        html.H2("File List"),
        html.Ul(id="file-list"),
    ],
    style={"max-width": "500px"},
)

#When a file is uploaded on Dash, save it into upload_directory
def save_file(name, content):
    print(content)
    with open(os.path.join(UPLOAD_DIRECTORY, name), "w") as text_file:
        text_file.write(content)

#List files in upload_directory
def uploaded_files():
    files = []
    for filename in os.listdir(UPLOAD_DIRECTORY):
        path = os.path.join(UPLOAD_DIRECTORY, filename)
        if os.path.isfile(path):
            files.append(filename)
    return files


def file_download_link(filename):
    """Create a Plotly Dash 'A' element that downloads a file from the app."""
    location = "/download/{}".format(urlquote(filename))
    return html.A(filename, href=location)



@app.callback(
    Output("file-list", "children"),
    [Input("button", "n_clicks")], 
    [State("input", "value"),
    State('filename_input', 'value')]
)
def update_output(n_clicks, value, filename_value):
    #If file is uploaded, save file in upload_directory
    if value is not None:
        save_file(filename_value + '.txt', value)

    #Return list of files in upload_directory
    files = uploaded_files()
    if len(files) == 0:
        return [html.Li("No files yet!")]
    else:
        #For every file in upload_directory, generate file download link
        return [html.Li(file_download_link(filename)) for filename in files]


if __name__ == "__main__":
    app.run_server(debug=False, port=8888)