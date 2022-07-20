from loading import LoadingMsg
from tokenize import String
from warnings import warn
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image
import requests
import json
import time
from urllib.request import urlretrieve
import os
import sys

WAIT_TIME = 3


class Dalle2:
    def __init__(self, auth_token: str) -> None:
        self.auth_token = auth_token

    def _get_headers(self, content_type="application/json"):
        return {
            "Authorization": "Bearer " + self.auth_token,
            "Content-Type": content_type,
        }

    def generate(
        self,
        prompt: str,
        max_retries=10,
        download=False,
        dir=".",
        name: str | None = None,
        links_only=False,
    ):
        url = "https://labs.openai.com/api/labs/tasks"
        headers = self._get_headers()
        body = {
            "task_type": "text2im",
            "prompt": {
                "caption": prompt,
                "batch_size": 6,
            },
        }

        print("Sending request...\n")
        res = requests.post(url, headers=headers, data=json.dumps(body))

        if res.status_code != 200:
            print("Request failed. Response:")
            print(res.text)
            return

        res_data = res.json()
        id = res_data["id"]

        print("Job created successfully")
        print(f"  id: {id}")
        print(f"  prompt: {prompt}\n")

        url = f"https://labs.openai.com/api/labs/tasks/{id}"
        images = None
        loading_msg = LoadingMsg("Generating images", "counter")
        for _ in range(max_retries):
            loading_msg.print()
            res_data = requests.get(url, headers=headers).json()
            if res_data["status"] == "succeeded":
                print("\nDone\n")
                images = res_data["generations"]["data"]
                break
            elif res_data["status"] == "failed":
                print("\nImage generation failed\n")
                break
            else:
                time.sleep(WAIT_TIME)

        if images is None:
            print(f"  task id: {id}")
            print(f"  url: {url}")
            return

        if download:
            self.download(images, dir, name)

        if links_only:
            return [image["generation"]["image_path"] for image in images]

        return images

    def get_task_results(self, task_id: str):
        url = f"https://labs.openai.com/api/labs/tasks/{task_id}"
        headers = self._get_headers()
        res_data = requests.get(url, headers=headers).json()
        if res_data["status"] == "succeeded":
            return res_data["generations"]["data"]
        else:
            print(f"Could not get image data from {task_id}")
            print("Response:")
            print(res_data)

    def download(self, image_data, dir, name: str | None = None):
        path = Path(os.path.expanduser(dir)).absolute()
        if not os.path.isdir(path):
            os.mkdir(path)

        print(f"Downloading to {path}...")

        images = []
        for i, image in enumerate(image_data):
            url = image["generation"]["image_path"]
            id = image["id"]
            im_name = id if not name else f"{name}{i+1}"
            image_path = path / f"{im_name}.webp"
            urlretrieve(url, image_path)
            images.append(image_path)
            print(f"  ✓ {im_name}")

        print("\nConverting images to jpeg...")
        for image in images:
            im = Image.open(image).convert("RGB")
            fname = os.path.splitext(image.name)[0] + ".jpg"
            im.save(path / fname, "jpeg")
            os.remove(image)

        print("Done.")

    def download_saved(self, page=1, lim=30, dir=".", name=None):
        url = f"https://labs.openai.com/api/labs/collections/collection-9t0G6wj87xFVvgsdNQkjwL6W/generations?page={page}&limit={lim}"
        headers = self._get_headers()

        res = requests.get(url, headers=headers)
        res_data = res.json()["data"]
        self.download(res_data, dir, name)
        print(res_data[0]["generation"]["image_path"])
        for item in res_data:
            generation = item["generation"]
            image_path = generation["image_path"]


if __name__ == "__main__":
    load_dotenv()
    token = os.environ.get("TOKEN", "")
    if not token:
        print("Make a .env file with the line:")
        print('TOKEN="sess-[YOUR-TOKEN]"')
        print(
            "\nYou can find your token by logging in to labs.openai.com, open the network tab in your browser console, generate an image, and check the authorization header in the POST request"
        )
    dalle = Dalle2(token)
    prompt = "peanut butter and jelly sandwich in the shape of a Rubik's cube, professional food photography"
    dalle.generate(prompt, download=True, dir="images", name="max-pbj")

    # image_data = dalle.get_task_results("task-H0ESQKWwAjO1Xl3k0HXbYfSS")
    # if image_data:
    #     dalle.download(image_data, "images", name="coffee")
    # dalle.download_saved(page=2, dir="test", name="saved2-")
