import os
import json
import pytest

from filelock import FileLock

from common import utils
from common.constant import Constant
from common.read_excel import ReadExcel
from common.context import Context
from common.logger import logger as log
from common.case_base import CaseBase

__all__ = [
    "pytest_generate_tests", "pytest_addoption", "pytest_configure",
    "pytest_xdist_auto_num_workers", "get_utils", "get_token"
]


def pytest_generate_tests(metafunc):
    log.info(f"generate fixture names {metafunc.fixturenames}")
    sheet = getattr(Context, "SHEET", None)
    if "data" in metafunc.fixturenames and sheet:
        # generate test cases
        conf = getattr(Context, "CONF")
        file_path = os.path.join(Constant.EXCEL_DIR, conf.get("file"))
        obj = ReadExcel(file_path, *sheet).read_obj()
        sheet = []
        [sheet.extend(case) for case in obj.values()]
        ids = [str(i.id) + i.title + "{" + f"{k}" + "}" for k, y in obj.items() for i in y]
        metafunc.parametrize(argnames="data", argvalues=sheet, ids=ids)


def pytest_addoption(parser):
    parser.addoption("-E", "--env", dest="env", action="store", default="test",
                     help="choice run environmental")  # 环境
    parser.addoption("-P", "--product", dest="product", action="store", default="G",
                     help="choice run product")  # 产品线
    parser.addoption("-S", "--sheet", dest="sheet", action="append", default=[],
                     help="Use cases that need to be run")  # 需要运行的用例
    parser.addoption("--mark", action="store", default=False, help="Run the marked use case sheet")


@pytest.mark.tryfirst
def pytest_configure(config):
    path = os.path.join(Constant.CONF_DIR, "config.json")
    with FileLock(path + ".lock"):
        with open(path, "r") as f:
            conf = json.load(f)
    env = config.getoption("env")
    product = config.getoption("product")
    conf = conf.get(product)
    setattr(Context, "CONF", conf)
    setattr(Context, "ENV", conf.get("env").get(env))
    log.init()
    mark = config.getoption("mark")
    sheet = config.getoption("sheet")
    remove_duplication(mark, sheet, product)


def pytest_xdist_auto_num_workers(config):
    sheet = config.getoption("sheet")
    mark = config.getoption("mark")
    product = config.getoption("product")
    sheet = remove_duplication(mark, sheet, product)
    return len(sheet)


def get_utils():
    utils_map = Context.CONF.get("utils")
    utils_obj = getattr(utils, utils_map)
    return utils_obj


def remove_duplication(mark, sheet, product):
    cases = getattr(Context, "SHEET", None)
    if not cases:
        if mark:
            sheet_path = os.path.join(Constant.CONF_DIR, "mark.json")
            with FileLock(sheet_path + ".lock"):
                with open(sheet_path, "r") as f:
                    sheets = json.load(f)
            try:
                sheet.extend(sheets.get(product).get(mark))
            except TypeError as e:
                log.error(f"Product or mark is wrong. Track: {e}")
                raise e
        sheet = list(set(sheet))
        sheet.sort()
        setattr(Context, "SHEET", sheet)
        return sheet
    else:
        return cases


def login(db, request, context):
    conf = getattr(context, "CONF")
    file = conf.get("file")
    file_path = os.path.join(Constant.EXCEL_DIR, file)
    sheet = conf.get("init")
    obj = ReadExcel(file_path, sheet).read_obj()
    for i in obj.values():
        CaseBase(db=db, request=request, context=context, utils=get_utils()).case(*i)


def get_token(worker_id, tmp_path_factory, db, request, context):
    if getattr(context, "CONF").get("init"):
        log.info(f"The data is initialized by worker_id {worker_id}")
        if worker_id == "master":
            login(db, request, context)
        else:
            root_tmp_dir = tmp_path_factory.getbasetemp().parent
            fn = root_tmp_dir / "data.json"
            with FileLock(str(fn) + ".lock", timeout=60):
                if fn.is_file():
                    token = json.loads(fn.read_text())
                    for k, y in token.items():
                        setattr(context, k, y)
                else:
                    login(db, request, context)
                    fn.write_text(json.dumps(context.__dict__))
