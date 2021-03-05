import os


class Constant:
    # 工作空间根目录
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

    # excel
    EXCEL_DIR = os.path.join(BASE_DIR, "data")

    # log
    LOGS_DIR = os.path.join(BASE_DIR, "logs")

    # conf
    CONF_DIR = os.path.join(BASE_DIR, "conf")

    # testcases
    CASES_DIR = os.path.join(BASE_DIR, "testcases")

    # report
    REPORT_DIR = os.path.join(BASE_DIR, "reports")

    # docs
    DOCS_DIR = os.path.join(BASE_DIR, "docs")