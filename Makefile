init:
	touch Procfile
	echo "web: gunicorn socialdistribution.wsgi --chdir Social-Distribution/socialdistribution" > Procfile

	heroku git:remote -a darkgoldenrod2
	heroku addons:create heroku-postgresql:essential-0 --app darkgoldenrod2
	heroku run "env" --app darkgoldenrod2
	heroku buildpacks:set heroku/python --app darkgoldenrod2

	git add .
	git commit -m "Add runtime.txt for Python version"
	git push heroku Development:main

	heroku run "python3.11 Social-Distribution/socialdistribution/manage.py diffsettings" --app darkgoldenrod2
	heroku run "python3.11 Social-Distribution/socialdistribution/manage.py migrate" --app darkgoldenrod2
	heroku run "python3.11 Social-Distribution/socialdistribution/manage.py createsuperuser" --app darkgoldenrod2

deploy:
	git add .
	git commit -m "Deploy"
	git push heroku Development:main
