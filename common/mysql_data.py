import pymysql
import time
import re
from common.logger import logger


class MySqlData:

    def __init__(self, host: str, user: str, password: str, database=None, port=3306, charset="utf8"):
        """
        Mysql connect init
        :param host:
        :param user:
        :param password:
        :param database: database name 可以不传 但sql里面必须要有 database.table
        :param port: default 3306
        :param charset: default utf8
        """

        # 三次重试连接
        for i in range(3):
            try:
                logger.debug("Database connection 【host: {}, database: {}】".format(host, database))
                # 创建数据库连接
                self.con = pymysql.connect(host=host, user=user, password=password,
                                           database=database, port=int(port), charset=charset,
                                           autocommit=True)  # 自动提交事物 mysql默认为repeatable read隔离策略
                logger.info("Database connect successfully 【host: {}, database: {}】".format(host, database))
                # 创建游标
                self.cur = self.con.cursor()
                logger.debug("Cursor created successfully")
                break
            except (pymysql.err.Error, TimeoutError) as e:
                logger.error("Database error: {}".format(e))
                continue

    def __del__(self):
        self.cur.close()
        self.con.close()

    def find_one(self, sql, expected=None, times=None) -> tuple:
        """
        Query all results
        :param times: loop times
        :param sql: Execute database expression -> str
        :param expected:
        :return: results -> tuple
        """
        res = None
        if not times:
            times = 20
        try:
            logger.info("Model: fetchone, SQL: 【{}】".format(sql))
            for i in range(times):
                row = self.cur.execute(sql)
                logger.info("row: {}".format(row))
                if not row:
                    time.sleep(6)
                    self.con.commit()
                    continue
                res = self.cur.fetchone()
                logger.info("result: {}".format(res))
                if not expected or res[0] == expected:
                    return res
                time.sleep(6)
                self.con.commit()
            return res
        except pymysql.err.InterfaceError as e:
            self.con.ping(reconnect=True)
            return self.find_one(sql, expected, times)
        except (pymysql.err.Error, TypeError) as e:
            logger.error("Database error rolling back: {}".format(e))
            self.con.rollback()
            raise e

    def find_all(self, sql) -> tuple:
        """
        Query all results
        :param sql: Execute database expression -> str
        :return: results -> tuple
        """
        try:
            logger.info("Model: fetchall, SQL: 【{}】".format(sql))
            self.con.ping(reconnect=True)
            for i in range(10):
                row = self.cur.execute(sql)
                logger.info("row: {}".format(row))
                if row:
                    break
                # self.con.commit()
                time.sleep(5)
            res = self.cur.fetchall()
            logger.info("result: {}".format(res))

            return res
        except (pymysql.err.Error, TypeError) as e:
            logger.error("Database error rolling back: {}".format(e))
            self.con.rollback()
            raise e

    def single_execute(self, sql) -> int:
        """
        execute rows
        :param sql:
        :return: execute rows -> int
        """
        try:
            logger.info("Model: single_execute, SQL: 【{}】".format(sql))
            row = self.cur.execute(sql)
            logger.info("row: {}".format(row))
            # self.con.commit()
            return int(row)
        except (pymysql.err.Error, TypeError) as e:
            logger.error("Database error rolling back: {}".format(e))
            self.con.rollback()
            raise e

    def multiple_execute(self, sql):
        p = r".+?[;]+?"
        sql_data = re.findall(p, sql)
        result = []
        for sql in sql_data:
            row = self.single_execute(sql)
            result.append(row)
        return result

    def write_data(self, sql):
        """
        write data
        :param sql:
        :return: None
        """
        try:
            logger.info("Model: write data, SQL: 【{}】".format(sql))
            row = self.cur.execute(sql)
            # self.con.commit()
            logger.info("execute row: {}".format(row))
        except (pymysql.err.Error, TypeError) as e:
            logger.error("Database error rolling back: {}".format(e))
            self.con.rollback()
            raise e
