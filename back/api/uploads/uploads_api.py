from flask import Blueprint, request, send_file
from werkzeug.utils import secure_filename

uploads_api = Blueprint('uploads', __name__)

@uploads_api.route('/')
def get_upload():
   filename = secure_filename(request.args.get("name"))
   return send_file('uploads/' + filename) 