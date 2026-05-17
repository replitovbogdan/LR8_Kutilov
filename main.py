rom flask import Flask
from waitress import serve
import psycopg2
import os

app = Flask(__name__)

def get_connection():
    username = os.environ.get('USER', 'runner')
    return psycopg2.connect(
        host="127.0.0.1",
        database="appdb",
        user=username
    )

@app.route("/")
def index():
    conn = get_connection()
    cursor = conn.cursor()
    result = []

    # 1. Версия PostgreSQL
    cursor.execute("SELECT version();")
    db_version = cursor.fetchone()[0]
    result.append(f"<h2>1. Версия PostgreSQL</h2><p>{db_version}</p>")

    # 2. Названия таблиц в базе данных
    cursor.execute("""
        SELECT schemaname, tablename
        FROM pg_catalog.pg_tables
        WHERE schemaname IN ('pg_catalog', 'information_schema')
        ORDER BY schemaname, tablename;
    """)
    tables = cursor.fetchall()
    table_names = [row[1] for row in tables]
    result.append("<h2>2. Таблицы в базе данных</h2><ul>")
    for t in table_names:
        result.append(f"<li>{t}</li>")
    result.append("</ul>")

    # 3. Названия столбцов 3 таблиц
    three_tables = ["pg_statistic", "pg_class", "pg_attribute"]
    result.append("<h2>3. Столбцы 3 таблиц</h2>")
    for tbl in three_tables:
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position;
        """, (tbl,))
        cols = [row[0] for row in cursor.fetchall()]
        result.append(f"<h3>{tbl}</h3><p>{', '.join(cols)}</p>")

    # 4. Все записи 3-х любых столбцов из выбранных таблиц
    result.append("<h2>4. Записи 3 столбцов</h2>")
    queries = [
        ("pg_statistic", "starelid, stanullfrac, stawidth"),
        ("pg_class",     "relname, relkind, reltuples"),
        ("pg_attribute", "attname, atttypid, attlen"),
    ]
    for tbl, cols in queries:
        cursor.execute(f"SELECT {cols} FROM {tbl} LIMIT 20;")
        rows = cursor.fetchall()
        result.append(f"<h3>{tbl} ({cols})</h3><table border='1'>")
        result.append(f"<tr>{''.join(f'<th>{c.strip()}</th>' for c in cols.split(','))}</tr>")
        for row in rows:
            result.append(f"<tr>{''.join(f'<td>{v}</td>' for v in row)}</tr>")
        result.append("</table>")

    # 5. Те же записи без дубликатов (DISTINCT)
    result.append("<h2>5. Записи без дубликатов (DISTINCT)</h2>")
    for tbl, cols in queries:
        cursor.execute(f"SELECT DISTINCT {cols} FROM {tbl} LIMIT 20;")
        rows = cursor.fetchall()
        result.append(f"<h3>{tbl} ({cols}) — DISTINCT</h3><table border='1'>")
        result.append(f"<tr>{''.join(f'<th>{c.strip()}</th>' for c in cols.split(','))}</tr>")
        for row in rows:
            result.append(f"<tr>{''.join(f'<td>{v}</td>' for v in row)}</tr>")
        result.append("</table>")

    # 6. starelid и stanullfrac из pg_statistic где stanullfrac BETWEEN 0.2 AND 0.8
    cursor.execute("""
        SELECT starelid, stanullfrac
        FROM pg_statistic
        WHERE stanullfrac BETWEEN 0.2 AND 0.8;
    """)
    rows = cursor.fetchall()
    result.append("<h2>6. pg_statistic: starelid, stanullfrac (0.2 – 0.8)</h2>")
    result.append("<table border='1'><tr><th>starelid</th><th>stanullfrac</th></tr>")
    for row in rows:
        result.append(f"<tr><td>{row[0]}</td><td>{row[1]}</td></tr>")
    result.append("</table>")

    # 7. starelid, stanullfrac, stadistinct где stadistinct = 1.0 ИЛИ 3.0
    cursor.execute("""
        SELECT starelid, stanullfrac, stadistinct
        FROM pg_statistic
        WHERE stadistinct IN (1.0, 3.0);
    """)
    rows = cursor.fetchall()
    result.append("<h2>7. pg_statistic: stadistinct = 1.0 или 3.0</h2>")
    result.append("<table border='1'><tr><th>starelid</th><th>stanullfrac</th><th>stadistinct</th></tr>")
    for row in rows:
        result.append(f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td></tr>")
    result.append("</table>")

    # 8. starelid, stanullfrac, stadistinct где stadistinct = 1.0, отсортировано по starelid ASC
    cursor.execute("""
        SELECT starelid, stanullfrac,


stadistinct
        FROM pg_statistic
        WHERE stadistinct = 1.0
        ORDER BY starelid ASC;
    """)
    rows = cursor.fetchall()
    result.append("<h2>8. pg_statistic: stadistinct = 1.0, сортировка по starelid ASC</h2>")
    result.append("<table border='1'><tr><th>starelid</th><th>stanullfrac</th><th>stadistinct</th></tr>")
    for row in rows:
        result.append(f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td></tr>")
    result.append("</table>")

    # 9. AVG(stawidth), MAX(stanullfrac), AVG(stadistinct), SUM(stadistinct) где starelid = 1247
    cursor.execute("""
        SELECT
            AVG(stawidth)     AS avg_stawidth,
            MAX(stanullfrac)  AS max_stanullfrac,
            AVG(stadistinct)  AS avg_stadistinct,
            SUM(stadistinct)  AS sum_stadistinct
        FROM pg_statistic
        WHERE starelid = 1247;
    """)
    row = cursor.fetchone()
    result.append("<h2>9. Агрегаты по pg_statistic WHERE starelid = 1247</h2>")
    result.append("<table border='1'>")
    result.append("<tr><th>AVG(stawidth)</th><th>MAX(stanullfrac)</th><th>AVG(stadistinct)</th><th>SUM(stadistinct)</th></tr>")
    result.append(f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td></tr>")
    result.append("</table>")

    cursor.close()
    conn.close()

    return "<html><body>" + "".join(result) + "</body></html>"

serve(app, host='0.0.0.0', port=5000, url_scheme='https')
