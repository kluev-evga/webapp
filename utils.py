import json
import re
from datetime import datetime

import cv2
import numpy as np
from fastapi import UploadFile

from database import templates_table


def validate_date_format(date_str):
    try:
        datetime.strptime(date_str, "%d.%m.%Y")
        return True
    except ValueError:
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False


def get_type(value: str):
    if re.match(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+', value):
        return "email"
    elif re.match(r'^\+7 \d{3} \d{3} \d{2} \d{2}$', value):
        return "phone"
    elif validate_date_format(value):
        return "date"
    else:
        return "text"


def find_matching_template(typed_data):
    for template in templates_table.all():
        template_fields = set(template.keys()) - {'name'}
        if all(
                field in typed_data and template[field] == typed_data[field]
                for field in template_fields
        ):
            return template['name']
    return None


async def read_request_body(file: UploadFile):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    qr_code_detector = cv2.QRCodeDetector()
    decoded_text, _, _ = qr_code_detector.detectAndDecode(image)
    try:
        decoded_data = json.loads(decoded_text)
        return decoded_data
    except json.JSONDecodeError:
        return {}
