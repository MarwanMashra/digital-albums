from app.database.mongo import Mongo, MongoSave, MongoLoad, MongoUpd, MongoRemove
from fastapi import FastAPI, Request, File, UploadFile, Form
from fastapi import Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .database import auth
from .database.auth import manager
import uvicorn
import aiofiles
from typing import List
import uuid
from base64 import b64encode

app = FastAPI()
coll_users = "users"
coll_albums = "albums"

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router)


@app.get("/upload", name="upload_page", response_class=HTMLResponse)
async def get_account_endpoint(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})


@app.get("/test_upload", name="test_upload_page", response_class=HTMLResponse)
async def get_account_endpoint(request: Request):
    return templates.TemplateResponse("test_upload.html", {"request": request})


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


async def get_username(request: Request):
    access_token = request.cookies.get("access-token")
    try:
        user = await manager.get_current_user(access_token)
    except:
        url = request.url_for("login_page")
        resp = RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)
        return resp
    return user["username"]


@app.post("/get_albums")
async def get_albums(request: Request):
    username = await get_username(request)
    account_coll = MongoLoad({"username": username})
    account = list(account_coll.retrieve(coll_users, limit=1))[0]
    return account["albums"]


@app.get("/album/{album_id}", name="album_page", response_class=HTMLResponse)
def album(request: Request, album_id: str):
    return templates.TemplateResponse(
        "album.html", {"request": request, "album_name": album_id}
    )


@app.post("/album/{album_id}")
def album(request: Request, album_id: str):
    if album_id[0] == "v":
        url_type = "view_url"
    elif album_id[0] == "e":
        url_type = "edit_url"
    else:
        return {"status": "error", "message": "Album not found"}
    albums_coll = MongoLoad({url_type: album_id})
    albums = list(albums_coll.retrieve(coll_albums, limit=1))
    if len(albums) == 0:
        return {"status": "error", "message": "Album not found"}
    if url_type == "view_url":
        albums[0].pop("edit_url")
    return {"album": albums[0], "status": "success"}


@app.post("/create_album", response_class=RedirectResponse)
async def create_album(request: Request, album_name: str = Form(...)):
    if album_name.strip() == "":
        return RedirectResponse(
            url=request.url_for("home_page"), status_code=status.HTTP_302_FOUND
        )
    username = await get_username(request)
    view_url = f"v{uuid.uuid4().hex}"
    edit_url = f"e{uuid.uuid4().hex}"
    album = {
        "name": album_name,
        "view_url": view_url,
        "edit_url": edit_url,
        "images": [],
    }
    documents = MongoSave([album])
    documents.storeindb(coll_albums)
    albums = await get_albums(request)
    albums[edit_url] = album_name
    db_update = MongoUpd({"username": username}, {"$set": {"albums": albums}})
    db_update.singleval_upd(coll_users)
    return RedirectResponse(url=f"/album/{edit_url}", status_code=status.HTTP_302_FOUND)


from imagekitio import ImageKit

image_kit = ImageKit(
    private_key="private_a0ZWNDtYh5zV1PafhpLhCOpyRic=",
    public_key="public_2Y5OO3C4BmvY4xpzn3dgEAk2qng=",
    url_endpoint="https://ik.imagekit.io/MyDigitalAlbums",
)


def add_images_album(url_list, album_id):
    if album_id[0] == "v":
        url_type = "view_url"
    elif album_id[0] == "e":
        url_type = "edit_url"
    else:
        return {"status": "error", "message": "Album not found"}
    try:
        db_update = MongoUpd(
            {url_type: album_id}, {"$addToSet": {"images": {"$each": url_list}}}
        )
        db_update.singleval_upd(coll_albums)
        return {"status": "success"}
    except:
        return {"status": "error", "message": "Album not found"}


@app.post("/upload", response_class=RedirectResponse)
async def upload(images: List[UploadFile] = File(None), album_id: str = Form(...)):
    url_list = []
    for image in images:
        image_name = image.filename
        image_content = await image.read()
        image_content_b64 = b64encode(image_content)
        upload_request = image_kit.upload_file(
            file=image_content_b64,
            file_name=image_name,
        )
        url_list.append(upload_request.url)
    response = add_images_album(url_list, album_id)
    if response["status"] == "error":
        return response
    return RedirectResponse(url=f"/album/{album_id}", status_code=status.HTTP_302_FOUND)


# @app.post("/create_album")
# async def create_album(album_name: str = Form(...)):


# 2Pv$5C,RDqUV9d[D
# @app.post("/test")
# def read_item(file: List[UploadFile] = File(None)):
#     if not file:
#         return "no file"
#     return {"name": file[0].filename}

# @app.post("/upload")
# async def upload(image: UploadFile = File(...)):
#     async with aiofiles.open("image.png", "wb") as out_file:
#         content = await image.read()  # async read
#         await out_file.write(content)  # async write
#     return {"images": image}


# @app.get("/", response_class=HTMLResponse)
# async def home(request: Request):
#     data = {"page": "Home page"}
#     return templates.TemplateResponse("index.html", {"request": request, "data": data})


# @app.get("/gallery", response_class=HTMLResponse)
# async def gallery(request: Request):
#     return templates.TemplateResponse("gallery.html", {"request": request})


# @app.get("/page/{page_name}", response_class=HTMLResponse)
# async def page(request: Request, page_name: str):
#     data = {"page": page_name}
#     return templates.TemplateResponse("index.html", {"request": request, "data": data})

# @app.get("/gallery", response_class=HTMLResponse)
# async def page(request: Request, page_name: str):
#     data = {"page": page_name}
#     return templates.TemplateResponse("index.html", {"request": request, "data": data})


# try:
#     contents = file.file.read()
#     with open(file.filename, "wb") as f:
#         f.write(contents)
# except Exception:
#     return {"message": "There was an error uploading the file"}
# finally:
#     file.file.close()

# return {"message": f"Successfully uploaded {file.filename}"}


if __name__ == "__main__":
    uvicorn.run(app)
