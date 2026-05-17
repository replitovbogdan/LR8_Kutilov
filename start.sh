# start Postgres
pg_ctl stop  # 2. Останавливает PostgreSQL если он уже запущен — нужно для чистого перезапуска, чтобы не было конфликта с предыдущим процессом

if [ ! -d "data/base" ]; then  # 4. Проверяет, существует ли директория data/base — она создаётся initdb при первой инициализации; если её нет — база ещё не инициализирована
  initdb                        # 5. Инициализирует новый кластер PostgreSQL: создаёт системные таблицы, конфиги и директорию data/base
  cp postgresql.conf.tpl data/postgresql.conf
  
  socker_dir="\/home\/runner\/${REPL_SLUG}\/postgres"
  
  sed -i "s/replace_unix_dir/${socker_dir}/" data/postgresql.conf  # 9. Заменяет placeholder replace_unix_dir в postgresql.conf на реальный путь к unix-сокету, сформированный из имени репла ($REPL_SLUG)
fi

pg_ctl -l /home/runner/${REPL_SLUG}/postgresql.log start

sleep 2

if ! psql -h 127.0.0.1 -d appdb -c '\q' 2>/dev/null; then
  psql -h 127.0.0.1 -d postgres -c "create database appdb;" 2>/dev/null || true
fi

# start Flask app
python main.py
