from fastapi import FastAPI, Request, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    data = {"page": "Home page"}
    return templates.TemplateResponse("index.html", {"request": request, "data": data})


@app.get("/page/{page_name}", response_class=HTMLResponse)
async def page(request: Request, page_name: str):
    data = {"page": page_name}
    return templates.TemplateResponse("index.html", {"request": request, "data": data})


@app.post("/upload")
def upload(file: UploadFile = File(...)):
    return templates.TemplateResponse("index.html")
    # try:
    #     contents = file.file.read()
    #     with open(file.filename, "wb") as f:
    #         f.write(contents)
    # except Exception:
    #     return {"message": "There was an error uploading the file"}
    # finally:
    #     file.file.close()

    # return {"message": f"Successfully uploaded {file.filename}"}
