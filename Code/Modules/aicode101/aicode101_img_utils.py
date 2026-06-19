from urllib.request import urlopen
from zipfile import ZipFile
import json
import os

def download_model_zip(download_link, save_path='./'):
    zipresp = urlopen(download_link)
    zipfile = open(save_path, 'wb')
    zipfile.write(zipresp.read())
    zipfile.close()

def unzip(zip_file, extract_path):
    zf = ZipFile(zip_file)
    zf.extractall(extract_path)
    zf.close()

def read_json(file_path):
    with open(file_path) as f:
        data = json.load(f)
    return data

def get_img_model(download_link):
    """
    This function downloads the image model from aicode101 and unzip it
    return: path of the image model dataset.json
    """
    cwd = os.getcwd()
    zip_save_path = cwd + '/model.zip'
    extract_path = cwd + '/'
    unzipped_json_path = extract_path + 'dataset.json'

    download_model_zip(download_link, zip_save_path)
    unzip(zip_save_path, extract_path)
    return unzipped_json_path


if __name__ == '__main__':
    download_link = 'https://aicode101.com/api/model/b952de40-dfc2-4726-8463-2e7f7b428753/download'

    unzipped_json_path = get_img_model(download_link)

    data = read_json(unzipped_json_path)
    print(len(data))

    for d in data:
        for k, v in d.items():
            if k == 'classId':
                print(v)
