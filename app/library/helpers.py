from imagekitio import ImageKit
from imagekitio.models.ListAndSearchFileRequestOptions import (
    ListAndSearchFileRequestOptions as SearchImg,
)

image_kit = ImageKit(
    private_key="private_a0ZWNDtYh5zV1PafhpLhCOpyRic=",
    public_key="public_2Y5OO3C4BmvY4xpzn3dgEAk2qng=",
    url_endpoint="https://ik.imagekit.io/MyDigitalAlbums",
)

coll_users = "users"
coll_albums = "albums"
