import os
import time
import jsonpath
import allure
from common.logger import logger


class ActionBase:

    def __init__(self, db, request, context, utils):
        self.db = db
        self.service = getattr(context, "ENV").get("service")
        self.request = request
        self.context = context
        self.logger = logger
        self.utils = utils(context, db)

    def wait_sleep(self, second=None):
        if second:
            self.logger.info(f"Waiting sleep {second}s")
            time.sleep(second)

    def join_url(self, service, api):  # TODO: 以后采用数据存储时可废弃
        try:
            return os.path.join(self.service[service], api)
        except KeyError as e:
            logger.error("The service is not configured")
            raise e

    def execute_sql(self, data, exe_field):
        for i in exe_field:
            value = getattr(data, i, None)
            if value:
                result = self.db.multiple_execute(value)
                return result


class CaseBase(ActionBase):

    def case(self, data):
        response = ""
        status = "error"
        try:
            self.wait_sleep(data.sleep)
            self.pre_execute_sql(data, ["setup_sql"])
            response = self.request_data(data)
            self.interface_assert_data(data, response)
            self.extract_data(data.extract_path, response.json())
            self.database_assert_data(data)
            self.teardown_execute_sql(data, ["teardown_sql"])
        except AssertionError as e:
            status = "Failed"
            self.logger.error("用例编号:{}[{}],运行结果:{} \n断言情况:\n{}".format(data.id, data.title, status, e))
            raise e
        else:
            status = "Successful"
            self.logger.info("用例编号:{}[{}],运行结果:{}".format(data.id, data.title, status))
        finally:
            if response:
                self.record_data(data, status, response)

    def initial_data(self, data, replace_field):
        with allure.step("数据准备"):
            self.logger.debug(f"数据准备字段: {replace_field}")
            for i in replace_field:
                value = getattr(data, i, None)
                if value:
                    self.logger.debug(f"正在处理数据 字段:[{i}]")
                    value = self.utils.replace_data(value)
                    setattr(data, i, value)

    def pre_execute_sql(self, data, exe_field):  # TODO: 暂不支持从预处理中提起参数
        with allure.step("前置sql执行"):
            self.initial_data(data, exe_field)
            self.logger.debug(f"前置执行字段:{exe_field}")
            result = self.execute_sql(data, exe_field)
            self.logger.debug(f"前置执行结果:{result}")
            return result

    def teardown_execute_sql(self, data, exe_field):  # TODO: 暂不支持从后处理中提起参数
        with allure.step("后置sql执行"):
            self.initial_data(data, exe_field)
            self.logger.debug(f"后置执行字段:{exe_field}")
            result = self.execute_sql(data, exe_field)
            self.logger.debug(f"后置执行结果:{result}")
            return result

    def request_data(self, data):
        with allure.step("发起请求"):
            self.initial_data(data, ["request_header", "request_body"])
            url = self.join_url(data.service, data.api)
            if data.data_type == "json":
                response = self.request.request_assert_by_jsonpath(method=data.method, url=url,
                                                                   expected=data.expected_body,
                                                                   wait_path=data.wait_path, times=data.wait_times,
                                                                   json=data.request_body, headers=data.request_header)
            elif data.data_type == "file":
                response = self.request.upload_stream(url=url, file_param=data.request_body["file_param"],
                                                      file_path=data.request_body["file_name"],
                                                      headers=data.request_header)
            else:
                raise ValueError("data_type not supported")
            return response

    def interface_assert_data(self, data, response):
        with allure.step("接口层断言"):
            self.initial_data(data, ["expected_body", "expected_header"])
            if data.assertion_body_path:
                for path in data.assertion_body_path:
                    actual = jsonpath.jsonpath(response.json(), path)
                    expected = jsonpath.jsonpath(data.expected_body, path)
                    allure.attach(str(actual), "body_actual:")
                    allure.attach(str(expected), "body_expected:")
                    self.logger.info(f"assert body: \nactual: {actual}\nexpected: {expected}")
                    assert actual == expected

            if data.assertion_headers_path:
                for path in data.assertion_headers_path:
                    actual = jsonpath.jsonpath(response.headers, path)
                    expected = jsonpath.jsonpath(data.expected_header, path)

                    allure.attach(str(actual), "headers_actual:")
                    allure.attach(str(expected), "headers_expected:")
                    self.logger.info(f"assert headers: \nactual: {actual}\nexpected: {expected}")
                    assert actual == expected

    def database_assert_data(self, data):
        if data.check_sql:
            with allure.step("数据层断言"):
                self.initial_data(data, ["check_sql", "assertion_sql_value"])
                res = self.db.find_one(data.check_sql, data.assertion_sql_value, times=data.wait_times)[0]
                allure.attach(str(res), "database actual:")
                allure.attach(str(data.assertion_sql_value), "database excepted:")
                self.logger.info(f"Data layer assert\nactual:[{res}]\nexcepted:[{data.assertion_sql_value}]")
                assert res == data.assertion_sql_value

    def extract_data(self, extract_path, response):
        if extract_path:
            with allure.step("提取参数"):
                for name, path in extract_path.items():
                    value = jsonpath.jsonpath(response, path)
                    if not value:
                        self.logger.error(f"提取失败 参数: [{name}] 值: [{value}] jsonpath: [{path}]")
                    else:
                        setattr(self.context, name, *value)
                        allure.attach(str(value), f"提取参数:{name} path: {path}")
                        self.logger.info(f"提取成功 参数: [{name}] 值: {value} jsonpath: [{path}]")

    def record_data(self, data, status, response):  # TODO: 此处可以拓展成数据库记录
        with allure.step("归档数据"):
            try:
                actual = {"row": data.id + 1, "column": 10, "msg": response.text}
                result = {"row": data.id + 1, "column": 11, "msg": status}
                datetime = {"row": data.id + 1, "column": 12, "msg": time.strftime("%y-%m-%d %H:%M:%S")}
                self.logger.info(f"{actual}\n{result}\n{datetime}")
            except AttributeError as e:
                self.logger.error(f"Case {str(data.id) + data.title} Running Failed! {e}")
