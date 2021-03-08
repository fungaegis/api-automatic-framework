import os
import time
import requests
import jsonpath
import filetype
from requests.sessions import session
from requests.adapters import HTTPAdapter
from common.logger import logger
from common.constant import Constant
from requests_toolbelt import MultipartEncoder


class HTTPRequest:

    def __init__(self):
        self.session = session()
        self.session.mount('http://', HTTPAdapter(max_retries=3))  # 连接失败重试3次
        self.session.mount('https://', HTTPAdapter(max_retries=3))

    def __del__(self):
        self.session.close()

    def request(self, method, url, json=None, headers=None, *args, **kwargs):
        self.session.request(self, method=method, url=url, json=json, headers=headers, *args, **kwargs)

    # 带token等请求头
    def request_assert_by_keyword(self, method, url, expected=None, *keyword, times=None, **kwargs):
        """
        Constructs a :class:`Request <Request>`, prepares it and sends it.
        Returns :class:`Response <Response>` object.
        :param times:
        :param method: method for the new :class:`Request` object.
        :param url: URL for the new :class:`Request` object.
        :param keyword:
        :param expected:
        """
        response = ""
        logger.info("正在请求：URL: {}, method: {}, 参数: {}".format(url, method, kwargs))
        if not times:
            times = 60
        for i in range(int(times)):
            try:
                response = self.session.request(method, url=url, timeout=60, **kwargs)
            except requests.exceptions.ConnectionError as e:
                logger.error("正在请求:URL: {} failed! {}".format(url, e))
                continue
            logger.info(response.text[:100])
            if keyword:
                r = response.json()
                e = expected
                try:
                    for n in keyword:
                        r = r[n]
                        e = e[n]
                    if r == e:
                        return response
                except KeyError:
                    continue
            else:
                return response
            time.sleep(6)
        return response

    def request_assert_by_jsonpath(self, method, url, wait_path=None, expected=None, times=None, **kwargs):
        logger.info("正在请求：URL: {}, method: {}, 参数: {}".format(url, method, kwargs))
        response = ""
        if not times:
            times = 60
        for i in range(int(times)):
            try:
                response = self.session.request(method, url=url, timeout=60, **kwargs)
                if response.status_code >= 400:
                    time.sleep(6)
                    continue
            except requests.exceptions.ConnectionError as e:
                logger.error("正在请求:URL: {} failed! {}".format(url, e))
                continue
            logger.info("Response:" + response.text[:100])
            if wait_path:
                e = expected
                r = jsonpath.jsonpath(response.json(), wait_path)
                e = jsonpath.jsonpath(e, wait_path)
                if not r and not e:
                    raise ValueError("jsonpath assert error!")
                if r == e:
                    logger.debug(f"waiting actual:{r} --- expected:{e}")
                    break
                logger.debug(f"restart waiting actual:{r} --- expected:{e}")
                time.sleep(6)
            else:
                break
        return response

    def upload_stream(self, url, file_param, file_path, headers, **kwargs):
        try:
            with open(file_path, "rb") as f:
                file_stream = f.read()
            file_name = os.path.split(file_path)[-1]
        except FileNotFoundError as e:
            file_name = file_path
            file_path = os.path.join(Constant.DOCS_DIR, file_path)
            logger.warning(f"error: {e}; Find default directory ({file_path})")
            with open(file_path, "rb") as f:
                file_stream = f.read()
        finally:
            mime = filetype.guess(file_path).mime  # found file MIME type
            if not mime:
                mime = "multipart/form-data"
            file = {"file": (file_name, file_stream, mime)}
            file.update(file_param)
            file = MultipartEncoder(fields=file)
            headers.update({"Content-Type": file.content_type})
            try:
                response = self.session.request("post", url=url, headers=headers, data=file, **kwargs)
            except requests.exceptions.ConnectionError as e:
                time.sleep(2)
                logger.error("正在请求上传文件 URL: {} failed! {}".format(url, e))
                response = self.upload_stream(url, file_param, file_path, headers, **kwargs)
            else:
                logger.info("正在请求上传文件 URL:{}, file_name:{}".format(url, file_path))
        return response
