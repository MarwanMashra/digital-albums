from app.database.mongo import Mongo, MongoSave, MongoLoad, MongoUpd, MongoRemove
from fastapi import FastAPI, Request, File, UploadFile, Form
from fastapi import Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.database import auth, album
from app.database.auth import manager
import uvicorn
from typing import List
from base64 import b64encode
from app.library.helpers import *
from app.database.album import add_images_album

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router)
app.include_router(album.router)


@app.get("/album", response_class=HTMLResponse)
@app.get("/", name="home_page", response_class=HTMLResponse)
async def get_account_endpoint(request: Request):
    # print cookies using manager
    access_token = request.cookies.get("access-token")
    try:
        user = await manager.get_current_user(access_token)
    except:
        url = request.url_for("login_page")
        resp = RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)
        return resp
    return templates.TemplateResponse(
        "index.html", {"request": request, "username": user["username"]}
    )


@app.post("/upload", response_class=RedirectResponse)
async def upload(images: List[UploadFile] = File(None), album_id: str = Form(...)):
    url_list = []
    for image in images:
        image_name = image.filename
        if image_name.strip() != "":  # avoid empty submissions
            image_content = await image.read()
            image_content_b64 = b64encode(image_content)
            upload_request = image_kit.upload_file(
                file=image_content_b64,
                file_name=image_name,
            )
            url_list.append(upload_request.url)
    if len(url_list) != 0:
        response = add_images_album(url_list, album_id)
        if response["status"] == "error":
            return response
    return RedirectResponse(url=f"/album/{album_id}", status_code=status.HTTP_302_FOUND)


@app.get("/gallery", response_class=HTMLResponse)
async def gallery(request: Request):
    return templates.TemplateResponse("gallery.html", {"request": request})


if __name__ == "__main__":
    uvicorn.run(app)
