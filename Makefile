init:
	touch Procfile
	echo "web: gunicorn socialdistribution.wsgi --chdir Social-Distribution/socialdistribution" > Procfile

	heroku git:remote -a darkgoldenrodtiana
	heroku addons:create heroku-postgresql:essential-0 --app darkgoldenrodtiana
	heroku run "env" --app darkgoldenrodtiana
# 	heroku buildpacks:set heroku/python --app darkgoldenrodtiana

	git add .
	git commit -m "Add runtime.txt for Python version"
	git push heroku Development:main

	heroku run "python3.11 Social-Distribution/socialdistribution/manage.py diffsettings" --app darkgoldenrodtiana
	heroku run "python3.11 Social-Distribution/socialdistribution/manage.py migrate" --app darkgoldenrodtiana
	heroku run "python3.11 Social-Distribution/socialdistribution/manage.py createsuperuser" --app darkgoldenrodtiana

deploy:
	git add .
	git commit -m "Deploy"
	git push heroku Development:main