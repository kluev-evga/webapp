from fastapi import FastAPI, File, UploadFile

from database import create_db
from utils import get_type, read_request_body, find_matching_template

create_db()

app = FastAPI(title="find_form_name_app")


@app.post("/get_form")
async def get_form(file: UploadFile = File(...)):
    decoded_data = await read_request_body(file)
    # данные в формате Dict[key, type]:
    typed_data = {field: get_type(value) for field, value in decoded_data.items() if field != "name"}
    matching_template_name = find_matching_template(typed_data)

    if matching_template_name:
        return {"template_name": matching_template_name}
    else:
        return typed_data
