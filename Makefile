init:
	touch Procfile
	echo "web: gunicorn socialdistribution.wsgi --chdir Social-Distribution/socialdistribution" > Procfile

	heroku git:remote -a darkgoldenrod3
	heroku addons:create heroku-postgresql:essential-0 --app darkgoldenrod3
	heroku run "env" --app darkgoldenrod3
	heroku buildpacks:set heroku/python --app darkgoldenrod3

	git add .
	git commit -m "Add runtime.txt for Python version"
	git push heroku Development:main

	heroku run "python3.11 Social-Distribution/socialdistribution/manage.py diffsettings" --app darkgoldenrod3
	heroku run "python3.11 Social-Distribution/socialdistribution/manage.py migrate" --app darkgoldenrod3
	heroku run "python3.11 Social-Distribution/socialdistribution/manage.py createsuperuser" --app darkgoldenrod3

static:
	heroku run "python3.11 Social-Distribution/socialdistribution/manage.py collectstatic"

superuser:
	heroku run "python3.11 Social-Distribution/socialdistribution/manage.py createsuperuser"

makemigrations:
	heroku run "python3.11 Social-Distribution/socialdistribution/manage.py makemigrations"

migrate:
	heroku run "python3.11 Social-Distribution/socialdistribution/manage.py migrate"

flush:
	heroku run "python3.11 Social-Distribution/socialdistribution/manage.py flush"

test_all:
	@echo "Running tests..."
	@python3.11 Social-Distribution/socialdistribution/manage.py test node.tests

tag-part3:
	@git checkout Production
	@git pull origin Production
	@git tag -a -s "part3" -m "Tagging the latest commit on the Production branch as part 3"
	@git push origin "part3"
	@echo "Tag 'part3' has been created and pushed to GitHub."

tag-part4:
	@git checkout Production
	@git pull origin Production
	@git tag -a -s "part4" -m "Tagging the latest commit on the Production branch as part 4"
	@git push origin "part4"
	@echo "Tag 'part4' has been created and pushed to GitHub."

tag-part5:
	@git checkout Production
	@git pull origin Production
	@git tag -a -s "part5" -m "Tagging the latest commit on the Production branch as part 5"
	@git push origin "part5"
	@echo "Tag 'part5' has been created and pushed to GitHub."

uuid:
	@heroku pg:reset --confirm darkgoldenrodtiana
	@heroku run "python3.11 Social-Distribution/socialdistribution/manage.py migrate"
	@heroku run "python3.11 Social-Distribution/socialdistribution/manage.py createsuperuser"