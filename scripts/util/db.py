import psycopg2
import psycopg2.extras
import config


def execute_sql_for_dict(query, values):
    print("executing query {} with values {}".format(query, values))
    con = None
    ret = None
    try:
        con = psycopg2.connect(database=config.postgres["database"],
                               user=config.postgres["user"],
                               password=config.postgres["password"],
                               host=config.postgres["host"],
                               port=config.postgres["port"])
        cursor = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(query, values)
        inter_ret = cursor.fetchall()
        ret = [dict(row) for row in inter_ret]
    except Exception as e:
        print(str(e))
        if con:
            con.rollback()
    finally:
        if con:
            con.close()
        return ret

