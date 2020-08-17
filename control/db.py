import psycopg2
import config


def execute_sql(query, values, logger, does_return_value=False):
    logger.debug("executing query {} with values {}".format(query, values))
    con = None
    res = None
    try:
        con = psycopg2.connect(database=config.postgres["database"],
                               user=config.postgres["user"],
                               password=config.postgres["password"],
                               host=config.postgres["host"],
                               port=config.postgres["port"])
        cursor = con.cursor()
        cursor.execute(query, values)
        if does_return_value:
            res = cursor.fetchall()
        con.commit()
    except Exception as e:
        logger.error(str(e))
        if con:
            con.rollback()
    finally:
        if con:
            con.close()
        return res
