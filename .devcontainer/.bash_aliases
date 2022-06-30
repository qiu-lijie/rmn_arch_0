alias dj-migrate='python manage.py makemigrations && python manage.py migrate'
alias dj-test='python manage.py test --keepdb'
alias dj-test-para='dj-test --parallel'
alias dj-test-fast='dj-test --parallel --exclude-tag e2e'
alias dj-test-clean='python manage.py test --noinput --parallel --exclude-tag e2e'
alias dj-shell='python manage.py shell'
alias dj-runserver='python manage.py runserver 0.0.0.0:8000'

# host alias
alias docker-stop='docker-compose stop'
alias docker-start='docker-compose up -d'
alias docker-restart='docker-compose restart'
alias docker-restart-se='docker-compose restart selenium'
alias docker-log='docker-compose logs --tail=0 -f web frontend'
alias docker-start-w-log='docker-start && docker-log'
alias web='docker-compose exec web bash'
alias web-log='docker-compose logs --tail=0 -f web'
alias fn='docker-compose exec frontend bash'
alias fn-log='docker-compose logs --tail=0 -f frontend'
alias db='docker-compose exec db psql --username=web --dbname=web_db'
alias test='docker-compose exec web bash -c "python manage.py test --parallel --noinput"'