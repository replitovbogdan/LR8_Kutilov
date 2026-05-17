{ pkgs }:  # Строка 1: Объявляет функцию, принимающую аргумент pkgs (набор пакетов Nixpkgs)

let         # Строка 2: Начинает блок let для создания локальных переменных

    nginxModified = pkgs.nginx.overrideAttrs (oldAttrs: rec {  # Строка 4: Создает модифицированную версию nginx, переопределяя атрибуты сборки
        configureFlags = oldAttrs.configureFlags ++ [
            "--http-client-body-temp-path=/home/runner/workspace/cache/client_body"
            "--http-proxy-temp-path=/home/runner/workspace/cache/proxy"
            "--http-fastcgi-temp-path=/home/runner/workspace/cache/fastcgi"
            "--http-uwsgi-temp-path=/home/runner/workspace/cache/uwsgi"
            "--http-scgi-temp-path=/home/runner/workspace/cache/scgi"
         ];
    });

in {        # Строка 14: Завершает блок let и возвращает набор атрибутов
    deps = [ # Строка 15: Объявляет атрибут deps со списком зависимостей
        nginxModified                      # Строка 16: Модифицированный nginx
        pkgs.python39                      # Строка 17: Python 3.9
        pkgs.python39Packages.flask        # Строка 18: Flask веб-фреймворк
        pkgs.python39Packages.waitress     # Строка 19: Waitress WSGI сервер
        pkgs.postgresql                    # Строка 20: PostgreSQL СУБД
        pkgs.python39Packages.psycopg2     # Строка 21: Адаптер PostgreSQL для Python
    ];
}
